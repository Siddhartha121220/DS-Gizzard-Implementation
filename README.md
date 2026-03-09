# Gizzard Router Dashboard

A distributed systems simulation built with **React**, **Python Flask**, and **Apache Thrift**. This project demonstrates consistent hashing, virtual node distribution, and dynamic RPC cluster management mirroring Twitter's (former) Gizzard architectural routing framework.

![Dynamic Management](frontend/public/dynamic_server.png)

## Features
- **Consistent Hashing**: A SHA-256 backed hash ring dynamically distributing traffic across $N$ simulated physical nodes.
- **Thrift RPC**: Inter-process communication between the Router Client and Storage Nodes utilizing Apache Thrift protocols. 
- **Dynamic Cluster Management**: Spin up, shut down, and rename full local shard sets dynamically through a visual React UI. 
- **Live Visualizations**: Visual mapping of the virtual ring topology via Chart.js.
- **Replication**: Automatic data replication across multiple nodes for fault tolerance.
- **Failover & Fault Tolerance**: Automatic node health monitoring, failure detection, and request failover to replica nodes with real-time dashboard. 

---

## 🚀 Getting Started

When you clone and run this application, it will dynamically bind to your local machine's hostname and act as a local distributed cluster node.

### 1. Prerequisites
- Python 3.8+
- Node.js (v16+) & npm
- Apache Thrift compiler (optional, if modifying `schema.thrift`)

### 2. Backend Setup
The backend serves as the Router API and hosts the python subprocesses simulating individual database shards.

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate
# Mac / Linux
source venv/bin/activate

pip install -r requirements.txt

# Start the Router
python run_all.py
```
> The Router API will boot up on `http://localhost:5000`. By default, **it will not start the simulated storage shards**. You will use the UI to boot them.

### 3. Frontend Setup
The frontend is a Vite + React application providing the visual management layer.

```bash
cd frontend
npm install

# Start the development server
npm run dev
```
> Open your browser to the local URL provided (usually `http://localhost:5173`).

---

## 🎮 Managing Your Server

Once the UI is running, scroll down to the **Physical Servers** section.
1. You will see your computer's hostname listed.
2. Click **Start Server** to dynamically spawn the backend Python Thrift storage subprocesses.
3. The visual indicator will turn **Green (UP)**.
4. You can click on your Hostname to rename your server block inline.
5. You can now use the **Send Tweet to Router** form at the top to fire simulated data into the backend. The Router will hash the Tweet ID, locate the correct virtual node, and dispatch the data via Thrift to the correct Shard over localhost ports.
6. The Physical Servers UI section will live-update to show which Tweets landed in which Shard.

---

## Architecture
- `backend/router_app.py`: The Flask API gateway managing global routing and subprocess lifecycles.
- `backend/router/consistent_hash.py`: The deterministic hashing logic that maps keys to nodes on a theoretical 360-degree ring.
- `backend/storage_node.py`: A lightweight Thrift Server that stores data locally in python memory arrays. 
- `backend/config/nodes_config.json`: The topology manifest mapping Shards to Host machines mapping to Ports.
- `backend/failover/`: Failover and fault tolerance module with health monitoring, automatic failover, and event logging.

---

## 🛡️ Failover & Fault Tolerance

The system includes a comprehensive failover module that automatically detects node failures and redirects requests to replica nodes.

### Key Features

**Health Monitoring**
- Background thread checks node health every 5 seconds via Thrift `heartbeat()` RPC
- Hybrid approach: periodic checks + immediate verification on request failure
- Gradual recovery: 3 consecutive successful heartbeats required before marking node ACTIVE

**Automatic Failover**
- **Read Failures**: Retry primary once, then automatically failover to replica node
- **Write Failures**: Write to replica when primary fails, routing unchanged
- Node status tracking: ACTIVE, DOWN, RECOVERING

**Real-Time Dashboard**
- Color-coded node status indicators (green=ACTIVE, red=DOWN, yellow=RECOVERING)
- Failover event log with detailed history
- Cluster health visualizations with Chart.js
- WebSocket-powered real-time updates

### Architecture

**Backend Components:**
```
backend/failover/
├── config.py                 # Configuration constants
├── node_registry.py          # Node status tracking with gradual recovery
├── node_health_monitor.py    # Background health checker (daemon thread)
├── event_logger.py           # Hybrid event logging (memory + file)
├── failover_manager.py       # Retry and failover logic
└── websocket_manager.py      # Real-time event broadcasting
```

**Frontend Components:**
```
frontend/src/
├── components/
│   ├── NodeStatusDashboard.jsx   # Node health display
│   ├── FailoverEventLog.jsx      # Event history table
│   └── ClusterHealthGraph.jsx    # Chart.js visualizations
└── hooks/
    └── useWebSocket.js           # WebSocket connection hook
```

### API Endpoints

- `GET /nodes/status` - Get status of all nodes (ACTIVE/DOWN/RECOVERING)
- `GET /nodes/health` - Get detailed health info (last heartbeat, recovery progress)
- `GET /failover/logs` - Get recent failover events (limit parameter supported)

### Testing Failover

**Scenario 1: Node Failure Detection**
1. Start all storage nodes via UI
2. Verify all nodes show ACTIVE (green) in dashboard
3. Stop one storage node (kill process)
4. Wait 5-10 seconds for health monitor to detect failure
5. Verify node status changes to DOWN (red) in real-time
6. Check failover event log for "node_down" event

**Scenario 2: Read Failover**
1. Ensure one node is DOWN
2. Send GET request for tweet stored on DOWN node
3. System automatically:
   - Retries primary once
   - Fails over to replica node
   - Returns data successfully
4. Verify "read_failover" event in log

**Scenario 3: Write Failover**
1. Ensure one node is DOWN
2. Send POST request for new tweet that hashes to DOWN node
3. System automatically writes to replica node
4. Verify "write_failover" event in log
5. Verify tweet stored on replica

**Scenario 4: Gradual Recovery**
1. With one node DOWN, restart the storage node process
2. Observe status changes in real-time:
   - First heartbeat: DOWN → RECOVERING (yellow)
   - Second heartbeat: Still RECOVERING
   - Third heartbeat: RECOVERING → ACTIVE (green)
3. Verify "node_up" event in log

### Configuration

Edit `backend/failover/config.py` to customize:
```python
HEARTBEAT_INTERVAL = 5      # seconds between health checks
HEARTBEAT_TIMEOUT = 2       # seconds to wait for heartbeat response
RECOVERY_THRESHOLD = 3      # consecutive successful heartbeats needed
MAX_RETRY_ATTEMPTS = 1      # number of retries before failover
REQUEST_TIMEOUT = 2         # seconds for read/write request timeout
```

### Event Logging

Failover events are logged with hybrid storage:
- **In-Memory**: Last 100 events for fast access
- **Persistent**: All events written to `backend/logs/failover_events.log`

Event types:
- `failover` - Successful failover to replica
- `recovery` - Node recovered and marked ACTIVE
- `health_check` - Health check status change

Actions:
- `read_failover` - Read redirected to replica
- `write_failover` - Write redirected to replica
- `node_down` - Node marked as DOWN
- `node_up` - Node recovered to ACTIVE

---
