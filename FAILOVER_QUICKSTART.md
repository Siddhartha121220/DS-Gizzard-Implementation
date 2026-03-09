# Failover Module Quick Start Guide

## Prerequisites
- Python 3.8+
- Node.js v16+
- All dependencies installed

## Installation

### Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

New dependencies added:
- `flask-socketio` - WebSocket support
- `python-socketio` - SocketIO client/server

### Frontend Dependencies
```bash
cd frontend
npm install
```

New dependency added:
- `socket.io-client` - WebSocket client

## Running the System

### 1. Start Backend (Terminal 1)
```bash
cd backend
python router_app.py
```

Expected output:
```
Health monitoring started
 * Running on http://0.0.0.0:5000
```

### 2. Start Frontend (Terminal 2)
```bash
cd frontend
npm run dev
```

Expected output:
```
VITE ready in XXX ms
Local: http://localhost:5173/
```

### 3. Access Dashboard
Open browser to `http://localhost:5173`

Scroll down to see the new **"Failover & Fault Tolerance Monitor"** section with:
- Node Health Status (with real-time connection indicator)
- Cluster Health Metrics (charts)
- Failover Event Log (table)

## Testing Failover

### Test 1: Node Failure Detection
1. Click "Start Server" in the Physical Servers section
2. Wait for all nodes to show ACTIVE (green) in the Failover dashboard
3. Open a new terminal and find the storage node process:
   ```bash
   ps aux | grep storage_node
   ```
4. Kill one process:
   ```bash
   kill <PID>
   ```
5. Watch the dashboard - within 5-10 seconds, the node will turn RED (DOWN)
6. Check the Failover Event Log for a "node_down" event

### Test 2: Read Failover
1. With one node DOWN, send a GET request for a tweet on that node:
   ```bash
   curl http://localhost:5000/tweet/<tweet_id>
   ```
2. The system will:
   - Retry the primary node once
   - Failover to the replica node
   - Return the data successfully
3. Check the Failover Event Log for a "read_failover" event (blue badge)

### Test 3: Write Failover
1. With one node DOWN, send a POST request via the UI form
2. If the tweet hashes to the DOWN node, it will automatically write to the replica
3. Check the Failover Event Log for a "write_failover" event (purple badge)

### Test 4: Gradual Recovery
1. Restart the stopped storage node:
   ```bash
   cd backend
   python storage_node.py --name Shard1 --port 9091
   ```
2. Watch the dashboard in real-time:
   - After 1st heartbeat: DOWN → RECOVERING (yellow)
   - After 2nd heartbeat: Still RECOVERING
   - After 3rd heartbeat: RECOVERING → ACTIVE (green)
3. Check the Failover Event Log for a "node_up" event (green badge)

## API Endpoints

### Node Status
```bash
# Get all node statuses
curl http://localhost:5000/nodes/status

# Get detailed health info
curl http://localhost:5000/nodes/health
```

### Failover Logs
```bash
# Get recent 50 events
curl http://localhost:5000/failover/logs

# Get recent 100 events
curl http://localhost:5000/failover/logs?limit=100
```

## Configuration

Edit `backend/failover/config.py` to customize:

```python
HEARTBEAT_INTERVAL = 5      # Health check frequency (seconds)
HEARTBEAT_TIMEOUT = 2       # Heartbeat response timeout (seconds)
RECOVERY_THRESHOLD = 3      # Heartbeats needed for recovery
MAX_RETRY_ATTEMPTS = 1      # Retries before failover
REQUEST_TIMEOUT = 2         # Request timeout (seconds)
```

## Troubleshooting

### WebSocket not connecting
- Check browser console for "WebSocket connected" message
- Verify backend is running with SocketIO (should see socketio logs)
- Check firewall settings for port 5000

### Nodes not showing in dashboard
- Ensure storage nodes are started via UI
- Check `GET /nodes/health` returns data
- Verify health monitor started (check backend logs)

### Failover not triggering
- Confirm node is actually DOWN (check process)
- Wait 5-10 seconds for health monitor to detect
- Check backend logs for health check failures
- Verify replica node exists and is ACTIVE

## Log Files

- **Failover Events**: `backend/logs/failover_events.log`
- **Backend Logs**: Console output from `router_app.py`
- **Frontend Logs**: Browser console

## Architecture Summary

**Backend Flow:**
1. NodeHealthMonitor checks nodes every 5s
2. NodeRegistry tracks status (ACTIVE/DOWN/RECOVERING)
3. On request failure, FailoverManager retries then redirects
4. EventLogger logs all events (memory + file)
5. WebSocketManager broadcasts updates to frontend

**Frontend Flow:**
1. useWebSocket hook connects to backend
2. Components receive real-time updates
3. Dashboard displays current status
4. Charts visualize cluster health
5. Event log shows failover history

## Success Indicators

✅ Backend shows "Health monitoring started"
✅ Frontend shows green connection indicator
✅ All nodes show ACTIVE (green) when running
✅ Node turns RED within 10s when stopped
✅ Failover events appear in log immediately
✅ Charts update in real-time
✅ Recovery shows YELLOW → GREEN progression

Enjoy your fault-tolerant distributed system! 🎉
