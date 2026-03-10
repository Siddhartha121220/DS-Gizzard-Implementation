import os
import sys
import json
import logging
import subprocess
import urllib.request
import urllib.error
import socket
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from router.consistent_hash import ConsistentHashRing
from replication.replication_manager import ReplicationManager
from failover.config import FailoverConfig
from failover.node_registry import NodeRegistry
from failover.node_health_monitor import NodeHealthMonitor
from failover.event_logger import EventLogger
from failover.failover_manager import FailoverManager
from failover.websocket_manager import WebSocketManager

from router_service import TweetService
from router_service.ttypes import *

app = Flask(__name__)
CORS(app)  # Allow frontend to call APIs
socketio = SocketIO(app, cors_allowed_origins="*")

# Load Node Configuration
config_path = os.path.join("config", "nodes_config.json")
try:
    with open(config_path, "r") as f:
        config = json.load(f)
except FileNotFoundError:
    config = {"servers": {}}

# Initialize Consistent Hash Ring
hash_ring = ConsistentHashRing(replicas=3)
servers_info = config.get("servers", {})

# Determine which server name is local to this machine.
# For multi-host setups, set LOCAL_SERVER_NAME (e.g., Laptop1/Laptop2/Laptop3) on each machine.
local_hostname = socket.gethostname()
local_server_name = os.environ.get("LOCAL_SERVER_NAME")
if local_server_name and local_server_name not in servers_info:
    local_server_name = None

# Back-compat: if LOCAL_SERVER_NAME is not set, map the first simulated server to this host.
# local_hostname = socket.gethostname()
# if "Laptop1" in servers_info:
#     servers_info[local_hostname] = servers_info.pop("Laptop1")

if not local_server_name and local_hostname in servers_info:
    local_server_name = local_hostname

# Flatten info for easy lookup: { 'Shard1': { 'host': ..., 'port': ..., 'server': 'Laptop1' } }
shard_lookup = {}

# Keep track of subprocesses for each server
server_processes = {}

# Add all shards to the ring and build lookup dictionary
for server_name, server_data in servers_info.items():
    for shard_name, shard_info in server_data.get("shards", {}).items():
        shard_lookup[shard_name] = {
            "host": shard_info["host"],
            "port": shard_info["port"],
            "server": server_name
        }
        hash_ring.add_node(shard_name)

# Initialize Replication Manager
replication_manager = ReplicationManager(hash_ring, shard_lookup)

# Initialize Failover System
failover_config = FailoverConfig()
node_registry = NodeRegistry(recovery_threshold=failover_config.RECOVERY_THRESHOLD)
event_logger = EventLogger(failover_config.FAILOVER_LOG_FILE, failover_config.MAX_MEMORY_EVENTS)
websocket_manager = WebSocketManager(socketio)
failover_manager = FailoverManager(shard_lookup, node_registry, event_logger, replication_manager, failover_config, websocket_manager)
health_monitor = NodeHealthMonitor(shard_lookup, node_registry, failover_config, websocket_manager)

# Auto-start health monitoring
health_monitor.start()

logging.basicConfig(level=logging.INFO)

def get_thrift_client(shard_name):
    """Create and return a connected Thrift client for the given shard."""
    shard_conf = shard_lookup.get(shard_name)
    if not shard_conf:
        return None, None
        
    transport = TSocket.TSocket(shard_conf['host'], shard_conf['port'])
    transport = TTransport.TBufferedTransport(transport)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = TweetService.Client(protocol)
    
    return client, transport

def get_remote_server_host(server_name):
    server = servers_info.get(server_name, {})
    shards = server.get("shards", {})
    for shard in shards.values():
        return shard.get("host")
    return None

def get_remote_server_status(server_name):
    host = get_remote_server_host(server_name)
    if not host:
        return "down"
    url = f"http://{host}:5000/servers/{server_name}/status"
    try:
        with urllib.request.urlopen(url, timeout=2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("status", "down")
    except Exception:
        return "down"

def proxy_remote_server_action(server_name, action):
    host = get_remote_server_host(server_name)
    if not host:
        return jsonify({"error": "Unknown server host"}), 500
    url = f"http://{host}:5000/servers/{server_name}/{action}"
    try:
        req = urllib.request.Request(
            url,
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return jsonify(data), 200
    except urllib.error.HTTPError as e:
        try:
            err_data = json.loads(e.read().decode("utf-8"))
        except Exception:
            err_data = {"error": "Remote error", "detail": str(e)}
        return jsonify(err_data), e.code
    except Exception as e:
        return jsonify({"error": "Remote unreachable", "detail": str(e)}), 502

@app.route('/tweet', methods=['POST'])
def store_tweet():
    data = request.json
    tweet_id = data.get('tweet_id')
    user_id = data.get('user_id')
    text = data.get('text')
    
    if not all([tweet_id, user_id, text]):
        return jsonify({"error": "Missing required fields"}), 400
        
    # Route using Consistent Hashing
    selected_node = hash_ring.get_node(tweet_id)
    hash_value = hash_ring._hash(str(tweet_id))
    
    if not selected_node:
        return jsonify({"error": "No available nodes"}), 503
        
    # Forward action via Thrift
    client, transport = get_thrift_client(selected_node)
    if not client:
        return jsonify({"error": f"Configuration missing for node {selected_node}"}), 500
        
    try:
        transport.open()
        success = client.storeTweet(tweet_id, user_id, text, False)
        transport.close()
        
        server_name = shard_lookup[selected_node]["server"]
        logging.info(f"TweetID {tweet_id} (Hash: {hash_value}) -> {selected_node} on {server_name}")
        
        # Trigger replication to secondary node
        replication_result = replication_manager.replicate_write(
            tweet_id, user_id, text, selected_node
        )
        
        return jsonify({
            "message": "Tweet stored successfully",
            "node": selected_node,
            "server": server_name,
            "tweet_id": tweet_id,
            "hash_value": str(hash_value),
            "replication": replication_result
        }), 201
    except Exception as e:
        import traceback
        traceback.print_exc()
        logging.error(f"Error connecting to node {selected_node}: {e}")
        
        # Handle write failure with failover
        failover_result = failover_manager.handle_write_failure(
            tweet_id, user_id, text, selected_node, e
        )
        
        if failover_result["success"]:
            server_name = shard_lookup[failover_result["node_used"]]["server"]
            return jsonify({
                "message": "Tweet stored successfully (failover)",
                "node": failover_result["node_used"],
                "server": server_name,
                "tweet_id": tweet_id,
                "hash_value": str(hash_value),
                "failover": True
            }), 201
        else:
            return jsonify({
                "error": f"Failed to store tweet: {failover_result.get('error', str(e))}",
                "failover_attempted": True
            }), 500

@app.route('/tweet/<tweet_id>', methods=['GET'])
def get_tweet(tweet_id):
    # Route using Consistent Hashing
    selected_node = hash_ring.get_node(tweet_id)
    
    if not selected_node:
        return jsonify({"error": "No available nodes"}), 503
        
    # Retrieve via Thrift
    client, transport = get_thrift_client(selected_node)
    if not client:
        return jsonify({"error": f"Configuration missing for node {selected_node}"}), 500
        
    try:
        transport.open()
        tweet_data_str = client.getTweet(tweet_id)
        transport.close()
        
        if not tweet_data_str:
            return jsonify({"error": "Tweet not found"}), 404
            
        tweet_data = json.loads(tweet_data_str)
        return jsonify(tweet_data), 200
    except Exception as e:
        logging.error(f"Error fetching from node {selected_node}: {e}")
        
        # Handle read failure with failover
        failover_result = failover_manager.handle_read_failure(
            tweet_id, selected_node, e
        )
        
        if failover_result["success"]:
            return jsonify({
                **failover_result["data"],
                "failover": True,
                "node_used": failover_result["node_used"]
            }), 200
        else:
            return jsonify({
                "error": f"Failed to retrieve tweet: {failover_result.get('error', str(e))}",
                "failover_attempted": True
            }), 500

@app.route('/hash-ring', methods=['GET'])
def get_hash_ring():
    ring_state = hash_ring.get_ring_state()
    # Enrich the nodes array with server information so the frontend can build exactly what it needs
    enriched_nodes = []
    for shard in ring_state["nodes"]:
        enriched_nodes.append({
            "shard": shard,
            "server": shard_lookup[shard]["server"]
        })
    
    return jsonify({
        "ring": ring_state["ring"],
        "nodes": enriched_nodes,
        "servers": servers_info # pass the full hierarchy for frontend visualization
    }), 200

@app.route('/shards', methods=['GET'])
def get_shards():
    """Fetch content of all active shards via Thrift."""
    result = {}
    for shard_name, info in shard_lookup.items():
        client, transport = get_thrift_client(shard_name)
        if not client:
            result[shard_name] = {"error": "configuration missing"}
            continue
            
        try:
            transport.open()
            tweets_str = client.getAllTweets()
            transport.close()
            
            result[shard_name] = {
                "server": info["server"],
                "tweets": json.loads(tweets_str) if tweets_str else []
            }
        except Exception as e:
            logging.error(f"Error fetching ALL from {shard_name}: {e}")
            result[shard_name] = {"error": "offline or RPC error"}

    return jsonify(result), 200

@app.route('/servers/status', methods=['GET'])
def get_servers_status():
    status = {}
    for server_name in servers_info.keys():
        # Remote status
        if local_server_name and server_name != local_server_name:
            remote_status = get_remote_server_status(server_name)
            status[server_name] = remote_status
            continue

        # Local status
        procs = server_processes.get(server_name, [])
        is_up = bool(procs) and all(p.poll() is None for p in procs)
        status[server_name] = "up" if is_up else "down"
    return jsonify(status), 200

@app.route('/servers/<server_name>/status', methods=['GET'])
def get_server_status(server_name):
    if server_name not in servers_info:
        return jsonify({"error": "Unknown server"}), 404
    procs = server_processes.get(server_name, [])
    is_up = bool(procs) and all(p.poll() is None for p in procs)
    return jsonify({"status": "up" if is_up else "down"}), 200

@app.route('/servers/<server_name>/start', methods=['POST'])
def start_server(server_name):
    if server_name not in servers_info:
        return jsonify({"error": "Unknown server"}), 404

    # Proxy to remote backend if this server is not local.
    if local_server_name and server_name != local_server_name:
        return proxy_remote_server_action(server_name, "start")
        
    procs = server_processes.get(server_name, [])
    if procs and all(p.poll() is None for p in procs):
        return jsonify({"message": "Server already running"}), 200
        
    new_procs = []
    python_exec = sys.executable
    for shard_name, info in servers_info[server_name].get("shards", {}).items():
        p = subprocess.Popen([python_exec, "storage_node.py", "--name", shard_name, "--port", str(info['port'])])
        new_procs.append(p)
        
    server_processes[server_name] = new_procs
    return jsonify({"message": f"Started {server_name}"}), 200

@app.route('/servers/<server_name>/stop', methods=['POST'])
def stop_server(server_name):
    if server_name not in servers_info:
        return jsonify({"error": "Unknown server"}), 404

    # Proxy to remote backend if this server is not local.
    if local_server_name and server_name != local_server_name:
        return proxy_remote_server_action(server_name, "stop")
        
    procs = server_processes.get(server_name, [])
    for p in procs:
        try:
            p.terminate()
            p.wait(timeout=2)
        except Exception as e:
            logging.error(f"Error terminating process: {e}")
            
    server_processes[server_name] = []
    return jsonify({"message": f"Stopped {server_name}"}), 200

@app.route('/servers/<server_name>/rename', methods=['POST'])
def rename_server(server_name):
    data = request.json
    new_name = data.get('new_name')
    if not new_name:
        return jsonify({"error": "New name is required"}), 400
        
    if server_name not in servers_info:
        return jsonify({"error": "Unknown server"}), 404
        
    # Update dict keys
    servers_info[new_name] = servers_info.pop(server_name)
    
    if server_name in server_processes:
        server_processes[new_name] = server_processes.pop(server_name)
        
    # Update nested shard lookup maps
    for shard_info in shard_lookup.values():
        if shard_info["server"] == server_name:
            shard_info["server"] = new_name
            
    return jsonify({"message": f"Server renamed to {new_name}"}), 200

@app.route('/replication/status', methods=['GET'])
def get_replication_status():
    """Fetch replication status for all tweets."""
    replication_map = replication_manager.get_replication_map()
    stats = replication_manager.get_replication_stats()
    
    return jsonify({
        "tweets": replication_map,
        "stats": stats
    }), 200

@app.route('/replication/status/<tweet_id>', methods=['GET'])
def get_tweet_replication_status(tweet_id):
    """Fetch replication status for a specific tweet."""
    status = replication_manager.get_replication_status(tweet_id)
    
    if not status:
        return jsonify({"error": f"Tweet {tweet_id} not found"}), 404
    
    return jsonify(status), 200

@app.route('/replication/map', methods=['GET'])
def get_replication_map():
    """Fetch the complete replication mapping for the dashboard."""
    replication_map = replication_manager.get_replication_map()
    
    # Format for frontend consumption
    formatted_map = []
    for rep in replication_map:
        formatted_map.append({
            "tweet_id": rep['tweet_id'],
            "primary_node": rep['primary_node'],
            "replica_node": rep['replica_node'],
            "timestamp": rep['timestamp'],
            "status": rep['status'],
            "primary_server": shard_lookup.get(rep['primary_node'], {}).get('server', 'Unknown'),
            "replica_server": shard_lookup.get(rep['replica_node'], {}).get('server', 'Unknown') if rep['replica_node'] else 'N/A'
        })
    
    return jsonify({
        "replication_map": formatted_map,
        "stats": replication_manager.get_replication_stats()
    }), 200

@app.route('/nodes/status', methods=['GET'])
def get_nodes_status():
    """Get status of all nodes."""
    return jsonify(node_registry.get_all_status()), 200

@app.route('/nodes/health', methods=['GET'])
def get_nodes_health():
    """Get detailed health info for all nodes."""
    return jsonify(node_registry.get_all_health_info()), 200

@app.route('/failover/logs', methods=['GET'])
def get_failover_logs():
    """Get recent failover events."""
    limit = request.args.get('limit', 50, type=int)
    return jsonify(event_logger.get_recent_events(limit)), 200

if __name__ == '__main__':
    # Default to localhost to avoid sandboxed bind restrictions.
    host = os.environ.get('ROUTER_HOST', '0.0.0.0')
    socketio.run(app, host=host, port=5000)
