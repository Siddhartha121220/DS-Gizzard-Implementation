# DS-Gizzard Multi-System Testing Guide

## Overview
Test the replication system across multiple physical machines for true distributed validation.

---

## Architecture Setup: Multiple Systems

### Example Setup
```
Machine 1 (192.168.1.100) - "Laptop1"
├── Flask Router (port 5000)
├── Shard1 (port 9091)
└── Shard2 (port 9092)

Machine 2 (192.168.1.101) - "Laptop2"
├── Shard3 (port 9093)
└── Shard4 (port 9094)

Machine 3 (192.168.1.102)
└── React Frontend (port 5173)
```

---

## Step 1: Network Configuration

### 1.1 Update Nodes Config (backend/config/nodes_config.json)

**Before (single machine):**
```json
{
  "servers": {
    "Laptop1": {
      "shards": {
        "Shard1": {"host": "127.0.0.1", "port": 9091},
        "Shard2": {"host": "127.0.0.1", "port": 9092}
      }
    },
    "Laptop2": {
      "shards": {
        "Shard3": {"host": "127.0.0.1", "port": 9093},
        "Shard4": {"host": "127.0.0.1", "port": 9094}
      }
    }
  }
}
```

**After (multi-machine):**
```json
{
  "servers": {
    "Laptop1": {
      "shards": {
        "Shard1": {"host": "192.168.1.100", "port": 9091},
        "Shard2": {"host": "192.168.1.100", "port": 9092}
      }
    },
    "Laptop2": {
      "shards": {
        "Shard3": {"host": "192.168.1.101", "port": 9093},
        "Shard4": {"host": "192.168.1.101", "port": 9094}
      }
    }
  }
}
```

**Key Change:** Replace `127.0.0.1` with actual IP addresses of each machine.

### 1.2 Find Your Machine IPs

**On Windows:**
```powershell
ipconfig
# Look for "IPv4 Address" under your network adapter
# Example output: 192.168.1.100
```

**On macOS/Linux:**
```bash
ifconfig
# or
ip addr
```

### 1.3 Update All Configuration Files

Update nodes_config.json on **all machines** with the same mapping:
- Machine 1: 192.168.1.100
- Machine 2: 192.168.1.101
- Machine 3: 192.168.1.102

---

## Step 2: Firewall Configuration

### 2.1 Open Required Ports

**Windows Firewall:**

```powershell
# For Flask Router (port 5000)
netsh advfirewall firewall add rule name="Flask Router" dir=in action=allow protocol=tcp localport=5000

# For Storage Nodes (9091-9094)
netsh advfirewall firewall add rule name="Storage Nodes" dir=in action=allow protocol=tcp localport=9091-9094

# For React Frontend (5173)
netsh advfirewall firewall add rule name="React Frontend" dir=in action=allow protocol=tcp localport=5173
```

**macOS/Linux:**
```bash
# UFW (Ubuntu)
sudo ufw allow 5000/tcp
sudo ufw allow 9091:9094/tcp
sudo ufw allow 5173/tcp
```

### 2.2 Verify Port Accessibility

**Test from another machine:**
```powershell
# Test if port is open
Test-NetConnection -ComputerName 192.168.1.100 -Port 9091
```

Expected: `TcpTestSucceeded : True`

---

## Step 3: Router Configuration

### 3.1 Allow External Connections in Flask

Modify `backend/router_app.py`:

```python
if __name__ == '__main__':
    # Change from: app.run(host='0.0.0.0', port=5000)
    # Already allows external connections!
    # 0.0.0.0 = listen on all network interfaces
    app.run(host='0.0.0.0', port=5000, debug=False)
```

**Verify:** This is already correct in the code (host='0.0.0.0')

### 3.2 Run Router on Designated Machine

**Machine 1 (192.168.1.100):**
```bash
cd backend
python router_app.py
# Server will be accessible at http://192.168.1.100:5000
```

---

## Step 4: Storage Nodes on Multiple Machines

### 4.1 Machine 1 (192.168.1.100) - Terminal 1 & 2

```bash
# Terminal 1: Start Shard1
python storage_node.py --port 9091 --name Shard1

# Terminal 2: Start Shard2
python storage_node.py --port 9092 --name Shard2
```

### 4.2 Machine 2 (192.168.1.101) - Terminal 1 & 2

First, **copy the entire backend folder** to Machine 2:
```bash
# On Machine 2, ensure you have the updated nodes_config.json
cd backend
python storage_node.py --port 9093 --name Shard3
python storage_node.py --port 9094 --name Shard4
```

**Important:** Machine 2 should have:
- Same Python dependencies (flask, thrift, etc.)
- Same backend code
- Updated nodes_config.json with correct IPs

---

## Step 5: Frontend on Third Machine (Optional)

### 5.1 Update Frontend API Endpoint

**Machine 3 (192.168.1.102)**

Modify `frontend/src/components/ReplicationDashboard.jsx` and all components:

Change:
```javascript
const response = await fetch('http://localhost:5000/replication/map');
```

To:
```javascript
const response = await fetch('http://192.168.1.100:5000/replication/map');
```

**Do this for all files:**
- `ReplicationDashboard.jsx`
- `ReplicaGraph.jsx`
- `NodeStorageViewer.jsx`
- `App.jsx`
- `TweetForm.jsx`
- `HashRingView.jsx`
- `ServerView.jsx`
- `RouterLogs.jsx`

### 5.2 Better Solution: Environment Variables

Create `frontend/.env`:
```
VITE_API_URL=http://192.168.1.100:5000
```

Update all fetch calls to use:
```javascript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';
const response = await fetch(`${API_URL}/replication/map`);
```

### 5.3 Run Frontend

**On Machine 3:**
```bash
cd frontend
npm run dev
# Frontend accessible at http://192.168.1.102:5173
```

---

## Step 6: Multi-System Testing Workflow

### 6.1 Systems Running

```
Machine 1 (192.168.1.100):
  ✓ Flask Router (http://192.168.1.100:5000)
  ✓ Shard1 (9091)
  ✓ Shard2 (9092)

Machine 2 (192.168.1.101):
  ✓ Shard3 (9093)
  ✓ Shard4 (9094)

Machine 3 (192.168.1.102):
  ✓ React Frontend (http://192.168.1.102:5173)
```

### 6.2 Testing Data Flow

**Test 1: Create Tweet from Frontend**
1. Open browser on Machine 3: http://192.168.1.102:5173
2. Create Tweet ID 101
3. **Expected Check:**
   - LocalLogs show routing decision
   - ReplicationDashboard shows replication to another node
   - One of the nodes on Machine 1 or 2 receives primary copy
   - Other node gets replica copy

**Test 2: Verify Cross-Machine Replication**
1. If primary goes to Shard1 (Machine 1), replica should go to Shard2 (Machine 1) OR Shard3 (Machine 2)
2. Use NodeStorageViewer to select different nodes across machines
3. Confirm same tweet exists on primary and replica

**Test 3: Network Failure Simulation**
1. Stop storage node on Machine 2 (Ctrl+C Shard3)
2. Create new tweet (should route to available shards)
3. System should still replicate to remaining nodes
4. Restart Shard3 - verify it catches up

---

## Step 7: Docker Setup (Alternative for Multi-Machine)

If you want to containerize and run on Docker:

### 7.1 Create Dockerfile (backend)

```dockerfile
FROM python:3.9
WORKDIR /app
COPY backend/ .
RUN pip install flask flask-cors thrift
EXPOSE 9091 9092 9093 9094 5000
CMD ["python", "router_app.py"]
```

### 7.2 Docker Compose (docker-compose.yml)

```yaml
version: '3.8'
services:
  router:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    networks:
      - gizzard-net

  shard1:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "9091:9091"
    command: python storage_node.py --port 9091 --name Shard1
    networks:
      - gizzard-net

  shard2:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "9092:9092"
    command: python storage_node.py --port 9092 --name Shard2
    networks:
      - gizzard-net

  shard3:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "9093:9093"
    command: python storage_node.py --port 9093 --name Shard3
    networks:
      - gizzard-net

  shard4:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "9094:9094"
    command: python storage_node.py --port 9094 --name Shard4
    networks:
      - gizzard-net

  frontend:
    build:
      context: frontend
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://router:5000
    networks:
      - gizzard-net
    depends_on:
      - router

networks:
  gizzard-net:
    driver: bridge
```

**Run with Docker:**
```bash
docker-compose up
```

---

## Step 8: Verification Across Systems

### 8.1 API Testing from Different Machines

**Machine 1:**
```powershell
# Test router from Machine 1
curl http://192.168.1.100:5000/replication/map

# Test storage node from any machine
curl http://192.168.1.100:9091/  # Should fail (not HTTP endpoint)
```

**Machine 2:**
```powershell
# Test if can reach router on Machine 1
curl http://192.168.1.100:5000/hash-ring
```

**Machine 3:**
```powershell
# Test frontend API calls work
curl http://192.168.1.100:5000/shards
```

### 8.2 Monitor Replication Across Machines

**Check Machine 1 logs:**
```
[Shard1] Storing tweet ID 101 from User user1
[Shard2] Storing tweet ID 101 from User user1 (replica=true)
```

**Check Machine 2 logs:**
```
[Shard3] Storing tweet ID 102 from User user1
[Shard4] Storing tweet ID 102 from User user1 (replica=true)
```

### 8.3 Database Consistency Check

Create script `backend/verify_consistency.py`:

```python
import json
import socket
from thrift.transport import TSocket, TTransport
from thrift.protocol import TBinaryProtocol

def get_tweets_from_shard(host, port):
    transport = TSocket.TSocket(host, port)
    transport = TTransport.TBufferedTransport(transport)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    from router_service import TweetService
    client = TweetService.Client(protocol)
    transport.open()
    tweets = json.loads(client.getAllTweets())
    transport.close()
    return tweets

# Check each shard
shards = {
    'Shard1': ('192.168.1.100', 9091),
    'Shard2': ('192.168.1.100', 9092),
    'Shard3': ('192.168.1.101', 9093),
    'Shard4': ('192.168.1.101', 9094),
}

all_tweets = {}
for shard_name, (host, port) in shards.items():
    tweets = get_tweets_from_shard(host, port)
    all_tweets[shard_name] = tweets
    print(f"{shard_name}: {len(tweets)} tweets")

# Verify replication factor = 2
for tweet_id in set(t['tweet_id'] for tweets in all_tweets.values() for t in tweets):
    count = sum(1 for tweets in all_tweets.values() for t in tweets if t['tweet_id'] == tweet_id)
    print(f"Tweet {tweet_id}: {count} copies (expected: 2)")
```

Run:
```bash
python backend/verify_consistency.py
```

---

## Step 9: Advanced Multi-System Scenarios

### 9.1 Latency Testing

Add delays to simulate network latency:

```python
# In replication_manager.py
import time

def _send_replica_write(self, tweet_id, user_id, text, replica_node):
    # Simulate network latency
    time.sleep(0.1)  # 100ms latency
    # ... rest of code
```

### 9.2 Failure Recovery

**Scenario 1: Stop Machine 2 (Storage nodes down)**
1. Stop Shard3 and Shard4 on Machine 2
2. Create new tweets - should still work with Shard1 and Shard2
3. ReplicationDashboard should show some replications to remaining shards
4. Restart Machine 2 - system recovers

**Scenario 2: Router Failure**
1. Kill Flask router on Machine 1
2. Frontend shows connection errors
3. Restart router
4. System recovers, no data loss

**Scenario 3: Network Partitioning**
1. Simulate by disabling network adapter on Machine 2
2. Tweets route to Machine 1 shards only
3. Re-enable network
4. System converges back to normal distribution

---

## Step 10: Performance Testing Across Network

### 10.1 Throughput Test

Create `backend/benchmark.py`:

```python
import requests
import time
from concurrent.futures import ThreadPoolExecutor

def create_tweet(tweet_id):
    url = 'http://192.168.1.100:5000/tweet'
    payload = {
        'tweet_id': str(tweet_id),
        'user_id': f'user{tweet_id % 10}',
        'text': f'Tweet #{tweet_id}'
    }
    start = time.time()
    r = requests.post(url, json=payload)
    elapsed = time.time() - start
    return elapsed

# Test 100 tweets with 10 concurrent threads
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(create_tweet, i) for i in range(100)]
    times = [f.result() for f in futures]

print(f"Average latency: {sum(times)/len(times)*1000:.2f}ms")
print(f"Min: {min(times)*1000:.2f}ms, Max: {max(times)*1000:.2f}ms")
print(f"Throughput: {len(times)/(sum(times)):.2f} tweets/sec")
```

Run:
```bash
python backend/benchmark.py
```

---

## Troubleshooting Multi-System Setup

### Issue: "Connection refused" between systems

**Solution:**
1. Check firewall rules are open
2. Verify IP addresses in nodes_config.json
3. Test connectivity: `ping 192.168.1.100`
4. Test port: `Test-NetConnection -ComputerName 192.168.1.100 -Port 9091`

### Issue: Frontend can't reach router

**Solution:**
1. Update API endpoint to router's IP
2. Check VITE_API_URL env variable
3. Verify router is listening on 0.0.0.0:5000
4. Test from Machine 3: `curl http://192.168.1.100:5000/hash-ring`

### Issue: Tweets replicate to wrong machines

**Solution:**
1. Verify nodes_config.json is identical on all systems
2. Check hash ring initialization is same
3. Logs should show replica node selection logic
4. Run verify_consistency.py script

### Issue: Data inconsistency across shards

**Solution:**
1. Ensure all replication operations complete
2. Check timestamps in replication logs
3. Run consistency verification script
4. Check for network timeouts in logs

---

## Multi-System Verification Checklist

- [ ] Network connectivity between all machines verified
- [ ] Firewall rules opened for required ports
- [ ] nodes_config.json updated with correct IPs on all systems
- [ ] Storage nodes on Machine 1: Shard1, Shard2 running
- [ ] Storage nodes on Machine 2: Shard3, Shard4 running
- [ ] Flask router on Machine 1 running and accessible from other machines
- [ ] React frontend on Machine 3 running
- [ ] Frontend API endpoint set correctly
- [ ] Create tweet → appears on primary + replica nodes
- [ ] Replica nodes distributed across machines
- [ ] ReplicationDashboard shows correct node names
- [ ] NodeStorageViewer shows tweets from all machines
- [ ] Network failure doesn't cause data loss
- [ ] Recovery works after machine restart
- [ ] Performance acceptable over network

---

## Quick Multi-System Setup Commands

### Machine 1 (192.168.1.100) - Update & Run

```bash
# Update config
# Edit backend/config/nodes_config.json with IPs

# Terminal 1 - Router
cd backend && python router_app.py

# Terminal 2 - Shard1
cd backend && python storage_node.py --port 9091 --name Shard1

# Terminal 3 - Shard2
cd backend && python storage_node.py --port 9092 --name Shard2
```

### Machine 2 (192.168.1.101) - Copy Code & Run

```bash
# Set up same code with updated nodes_config.json
cd backend

# Terminal 1 - Shard3
python storage_node.py --port 9093 --name Shard3

# Terminal 2 - Shard4
python storage_node.py --port 9094 --name Shard4
```

### Machine 3 (192.168.1.102) - Update & Run

```bash
# Update API endpoint in frontend
# Edit frontend/.env: VITE_API_URL=http://192.168.1.100:5000

cd frontend && npm run dev
# Open http://192.168.1.102:5173
```

---

## Expected Results

✅ Tweets created on Machine 3 frontend  
✅ Routed to shards on Machine 1 or 2  
✅ Replicated between machines  
✅ Dashboard shows cross-machine replication  
✅ NodeStorageViewer shows data from all machines  
✅ Network delays don't break consistency  
✅ Machine failures don't lose data  
