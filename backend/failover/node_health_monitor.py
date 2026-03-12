"""
Node Health Monitor Module
Background service for periodic health checks via Thrift heartbeat RPC.
"""
import threading
import time
import logging
import json
import sys
sys.path.append('gen-py')

from thrift.transport import TSocket, TTransport
from thrift.protocol import TBinaryProtocol
from router_service import TweetService


class NodeHealthMonitor:
    """Background health monitoring service with periodic heartbeat checks."""
    
    def __init__(self, shard_lookup, node_registry, event_logger, config, websocket_manager=None):
        """
        Initialize health monitor.
        
        Args:
            shard_lookup: Dict mapping shard names to {host, port, server} info
            node_registry: NodeRegistry instance for status tracking
            event_logger: EventLogger instance for failover logging
            config: FailoverConfig instance
            websocket_manager: Optional WebSocketManager for real-time updates
        """
        self.shard_lookup = shard_lookup
        self.node_registry = node_registry
        self.event_logger = event_logger
        self.config = config
        self.websocket_manager = websocket_manager
        self.running = False
        self.monitor_thread = None
        
        # Initialize all nodes in registry
        for shard_name in shard_lookup.keys():
            node_registry.initialize_node(shard_name)
    
    def start(self):
        """Start background monitoring thread."""
        if self.running:
            logging.warning("Health monitor already running")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        # Log startup event
        self.event_logger.log_event(
            "health_check", None, "system", None, "monitor_started",
            "Node health monitoring background service started"
        )
        logging.info("Health monitoring started")
    
    def stop(self):
        """Stop background monitoring thread."""
        if not self.running:
            return
        
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=self.config.HEARTBEAT_INTERVAL + 1)
        logging.info("Health monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop that checks all nodes periodically."""
        while self.running:
            for shard_name in self.shard_lookup.keys():
                self._check_node_health(shard_name)
            time.sleep(self.config.HEARTBEAT_INTERVAL)
    
    def _check_node_health(self, shard_name):
        """
        Check health of a single node via Thrift heartbeat.
        
        Args:
            shard_name: Name of the shard to check
        """
        shard_info = self.shard_lookup.get(shard_name)
        if not shard_info:
            return
        
        host = shard_info.get('host', '127.0.0.1')
        port = shard_info.get('port')
        
        try:
            # Create Thrift client with timeout
            transport = TSocket.TSocket(host, port)
            transport.setTimeout(self.config.HEARTBEAT_TIMEOUT * 1000)  # milliseconds
            transport = TTransport.TBufferedTransport(transport)
            protocol = TBinaryProtocol.TBinaryProtocol(transport)
            client = TweetService.Client(protocol)
            
            transport.open()
            response = client.heartbeat()
            transport.close()
            
            # Parse response
            data = json.loads(response)
            if data.get('status') == 'alive':
                old_status = self.node_registry.get_status(shard_name)
                self.node_registry.record_success(shard_name)
                new_status = self.node_registry.get_status(shard_name)
                
                # Log event if status changed
                if old_status != new_status:
                    self.event_logger.log_event(
                        "health_check", None, shard_name, None, 
                        f"node_status_change_{new_status.value.lower()}",
                        f"Node {shard_name} status changed from {old_status.value} to {new_status.value}"
                    )
                
                # Emit WebSocket event if status changed
                if self.websocket_manager and old_status != new_status:
                    health_info = self.node_registry.get_health_info(shard_name)
                    self.websocket_manager.emit_node_status_update(
                        shard_name, new_status.value, health_info
                    )
                
                logging.debug(f"[HealthCheck] {shard_name} is alive")
            else:
                self.node_registry.record_failure(shard_name)
                logging.warning(f"[HealthCheck] {shard_name} returned unexpected status")
        
        except Exception as e:
            old_status = self.node_registry.get_status(shard_name)
            self.node_registry.record_failure(shard_name)
            new_status = self.node_registry.get_status(shard_name)
            
            # Log event if status changed to DOWN
            if old_status != new_status and new_status.value == "DOWN":
                self.event_logger.log_event(
                    "health_check", None, shard_name, None, "node_down",
                    f"Node {shard_name} marked as DOWN due to: {str(e)}"
                )
            
            # Emit WebSocket event if status changed
            if self.websocket_manager and old_status != new_status:
                health_info = self.node_registry.get_health_info(shard_name)
                self.websocket_manager.emit_node_status_update(
                    shard_name, new_status.value, health_info
                )
            
            logging.warning(f"[HealthCheck] {shard_name} failed: {str(e)}")
    
    def check_node_now(self, shard_name):
        """
        Immediate health check for a specific node (on-demand).
        
        Args:
            shard_name: Name of the shard to check
            
        Returns:
            True if node is healthy, False otherwise
        """
        shard_info = self.shard_lookup.get(shard_name)
        if not shard_info:
            return False
        
        host = shard_info.get('host', '127.0.0.1')
        port = shard_info.get('port')
        
        try:
            transport = TSocket.TSocket(host, port)
            transport.setTimeout(self.config.HEARTBEAT_TIMEOUT * 1000)
            transport = TTransport.TBufferedTransport(transport)
            protocol = TBinaryProtocol.TBinaryProtocol(transport)
            client = TweetService.Client(protocol)
            
            transport.open()
            response = client.heartbeat()
            transport.close()
            
            data = json.loads(response)
            return data.get('status') == 'alive'
        
        except Exception:
            return False
