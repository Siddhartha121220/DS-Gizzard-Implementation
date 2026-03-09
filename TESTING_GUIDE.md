# DS-Gizzard Replication System - Testing Guide

## Prerequisites
- Python 3.7+
- Node.js & npm
- Flask, Thrift Python bindings installed
- React development environment ready

## Step-by-Step Testing Instructions

### Phase 1: Environment Setup

#### 1.1 Install Python Dependencies
```bash
# In the backend directory
pip install flask flask-cors thrift
```

#### 1.2 Install Frontend Dependencies
```bash
# In the frontend directory
npm install
# or
npm ci
```

#### 1.3 Verify Thrift Code Generation
Make sure the `gen-py` directory exists in backend with generated Thrift files:
```bash
backend/
├── gen-py/
│   └── router_service/
│       ├── __init__.py
│       ├── TweetService.py
│       └── ttypes.py
```

---

### Phase 2: Backend Startup

#### 2.1 Terminal 1 - Start Flask Router App
```bash
cd backend
python router_app.py
```
Expected output:
```
WARNING in app.run_simple (...)
 * Running on http://0.0.0.0:5000
 * Press CTRL+C to quit
```

#### 2.2 Terminal 2 - Start Storage Node 1 (Shard1)
```bash
cd backend
python storage_node.py --port 9091 --name Shard1
```
Expected output:
```
INFO:root:Initialized Storage Node: Shard1
INFO:root:Starting Shard1 on port 9091...
```

#### 2.3 Terminal 3 - Start Storage Node 2 (Shard2)
```bash
cd backend
python storage_node.py --port 9092 --name Shard2
```
Expected output:
```
INFO:root:Initialized Storage Node: Shard2
INFO:root:Starting Shard2 on port 9092...
```

#### 2.4 Terminal 4 - Start Storage Node 3 (Shard3)
```bash
cd backend
python storage_node.py --port 9093 --name Shard3
```

#### 2.5 Terminal 5 - Start Storage Node 4 (Shard4)
```bash
cd backend
python storage_node.py --port 9094 --name Shard4
```

**Checkpoint:** All 4 storage nodes should be running and listening.

---

### Phase 3: Frontend Startup

#### 3.1 Terminal 6 - Start React Development Server
```bash
cd frontend
npm run dev
```
Expected output:
```
  VITE v4.x.x  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

---

### Phase 4: Testing Routing & Replication

#### 4.1 Open Browser
Navigate to: **http://localhost:5173/**

You should see the Gizzard Router Dashboard with:
- TweetForm (left)
- HashRingView (center-top)
- RouterLogs (center-bottom)
- ServerView (shows all 4 shards)
- Replication Dashboard (new)
- ReplicaGraph (new)
- NodeStorageViewer (new)

#### 4.2 Create First Tweet
In the **TweetForm**:
- Tweet ID: `101`
- User ID: `user1`
- Text: `Hello Gizzard Distribution!`

Click **Post Tweet**

**Expected Results:**
1. RouterLogs shows routing entry: `Tweet 101 → Shard1`
2. TweetForm confirms "Tweet stored successfully"
3. Response includes replication info

#### 4.3 Check Replication Dashboard
Scroll to **Replication Dashboard** section:
- Should show entry for Tweet 101
- Primary Node: `Shard1` (or whichever was selected)
- Replica Node: `Shard2` (next node clockwise)
- Status: `SUCCESS`

#### 4.4 Verify in Node Storage Viewer
In **NodeStorageViewer**:
1. Select `Shard1` from dropdown
   - Should show Tweet 101 with Type: **Primary**
2. Select the replica node (next one, e.g., `Shard2`)
   - Should show Tweet 101 with Type: **Replica**

#### 4.5 Create Multiple Tweets
Create 3-4 more tweets with different IDs:

```
Tweet 102: user1, "Testing replication #2"
Tweet 103: user2, "Another distributed tweet"
Tweet 104: user3, "Final test tweet"
```

**Expected Pattern:**
- Tweet 101 → Primary: Shard1, Replica: Shard2
- Tweet 102 → Primary: Shard1, Replica: Shard2 (or different based on hash)
- Tweet 103 → Primary: Shard2, Replica: Shard3
- Tweet 104 → Primary: Shard3, Replica: Shard4

---

### Phase 5: Verify Data Distribution

#### 5.1 Check ReplicaGraph
1. Switch to **Bar Chart** view
2. Should see:
   - Shard1: Some primary, some replica
   - Shard2: Some primary, some replica
   - Shard3: Some primary, some replica
   - Shard4: Some primary, some replica

3. Stats cards should show:
   - Total Tweets: 4
   - Successful Replications: 4
   - Failed Replications: 0

#### 5.2 Inspect Each Node
In **NodeStorageViewer**:
1. Select each shard (Shard1, Shard2, Shard3, Shard4)
2. For each, verify:
   - **Primary tweets**: ~50% of tweets
   - **Replica tweets**: ~50% of tweets (from other primary nodes)
   - Total tweets = Primary + Replica

#### 5.3 Verify Replication Table
In **ReplicationDashboard** table:
- Scroll through all entries
- Each row should have:
  - Tweet ID
  - Primary Node (e.g., Shard1)
  - Replica Node (next node, e.g., Shard2)
  - Status: SUCCESS
  - Different servers assigned correctly

---

### Phase 6: Advanced Testing

#### 6.1 Test API Directly (Optional)
Open a new terminal and test API endpoints:

```bash
# Test replication status for all tweets
curl http://localhost:5000/replication/map

# Test specific tweet
curl http://localhost:5000/replication/status/101

# Get all shards content
curl http://localhost:5000/shards

# Get hash ring
curl http://localhost:5000/hash-ring
```

#### 6.2 Simulate High Volume
Create 10+ tweets rapidly:
- Create tweets 201-210 in quick succession
- Monitor ReplicaGraph updates in real-time
- Verify no tweets are missed
- Check dashboard auto-polling works (updates every 3s)

#### 6.3 Filter Testing in NodeStorageViewer
For any selected node:
- Click **All** - should show all tweets
- Click **Primary** - should show only primary copies
- Click **Replica** - should show only replica copies
- Toggle filters and verify counts

#### 6.4 Check Server Status
In **ServerView** section:
- Should show all servers as "up"
- Try stopping one storage node (Ctrl+C)
- Try creating a tweet - should still work (use another shard)
- Restart the node from ServerView buttons or terminal

---

### Phase 7: Troubleshooting

#### Issue: "Connection refused" errors
- **Check:** All 4 storage nodes are running on ports 9091-9094
- **Fix:** Start missing nodes in new terminals

#### Issue: Replication Dashboard shows "Loading..." indefinitely
- **Check:** Flask router is running on port 5000
- **Fix:** Start Flask app: `python router_app.py` in backend

#### Issue: No tweets appear in ServerView
- **Check:** Storage nodes are receiving Thrift calls
- **Look at:** Terminal logs for each storage node
- **Verify:** Ports 9091-9094 are accessible

#### Issue: Replication shows "FAILED" status
- **Check:** Replica node is running and connected
- **Check:** Thrift connection is successful
- **Look at:** Storage node terminal for RPC errors

#### Issue: frontend shows blank or "No data"
- **Check:** Frontend is running on http://localhost:5173
- **Check:** Browser console for API errors (F12)
- **Fix:** Restart frontend: `npm run dev`

---

### Phase 8: Verification Checklist

- [ ] All 4 storage nodes running (ports 9091-9094)
- [ ] Flask router running (port 5000)
- [ ] React frontend running (port 5173)
- [ ] TweetForm successfully creates tweets
- [ ] RouterLogs shows routing decisions
- [ ] ReplicationDashboard shows all tweets replicated
- [ ] Each tweet appears on primary + 1 replica node
- [ ] ReplicaGraph displays correct distribution
- [ ] NodeStorageViewer filters work correctly
- [ ] Statistics update in real-time
- [ ] No error messages in browser console
- [ ] All API endpoints respond correctly

---

### Phase 9: Performance Check

**Create 20 tweets rapidly:**
```
Measure:
- Time to replicate each tweet
- Total throughput
- Dashboard responsiveness
- Database consistency
```

**Expected Performance:**
- Replication should complete within 100-500ms per tweet
- Dashboard updates within 3 seconds
- All 20 tweets visible across nodes
- Zero data loss

---

## Success Criteria

✅ All tweets created successfully  
✅ Each tweet replicated to exactly 2 nodes (primary + 1 replica)  
✅ Replication metadata tracked and displayed  
✅ Dashboard auto-updates every 3 seconds  
✅ Charts show correct distribution  
✅ Node viewer shows accurate tweet counts  
✅ No errors in console or logs  
✅ System handles multiple concurrent writes  

## Quick Start Commands (Copy-Paste)

```bash
# Terminal 1
cd backend && python router_app.py

# Terminal 2
cd backend && python storage_node.py --port 9091 --name Shard1

# Terminal 3
cd backend && python storage_node.py --port 9092 --name Shard2

# Terminal 4
cd backend && python storage_node.py --port 9093 --name Shard3

# Terminal 5
cd backend && python storage_node.py --port 9094 --name Shard4

# Terminal 6
cd frontend && npm run dev
```

Then visit: **http://localhost:5173/**
