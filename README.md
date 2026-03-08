# Gizzard Router Dashboard

A distributed systems simulation built with **React**, **Python Flask**, and **Apache Thrift**. This project demonstrates consistent hashing, virtual node distribution, and dynamic RPC cluster management mirroring Twitter's (former) Gizzard architectural routing framework.

![Dynamic Management](frontend/public/dynamic_server.png)

## Features
- **Consistent Hashing**: A SHA-256 backed hash ring dynamically distributing traffic across $N$ simulated physical nodes.
- **Thrift RPC**: Inter-process communication between the Router Client and Storage Nodes utilizing Apache Thrift protocols. 
- **Dynamic Cluster Management**: Spin up, shut down, and rename full local shard sets dynamically through a visual React UI. 
- **Live Visualizations**: Visual mapping of the virtual ring topology via Chart.js. 

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
