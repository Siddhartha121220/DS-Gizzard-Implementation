import subprocess
import time
import sys
import json
import os

def start_services():
    processes = []
    
    # Load config
    config_path = os.path.join("config", "nodes_config.json")
    with open(config_path, "r") as f:
        config = json.load(f)
        
    # Start storage nodes (now handled dynamically by router_app.py via UI)
    python_exec = sys.executable
        
    env = os.environ.copy()
    env["PYTHONPATH"] = "gen-py" + (os.pathsep + env["PYTHONPATH"] if "PYTHONPATH" in env else "")

    print("Starting router service on port 5000...")
    p_router = subprocess.Popen([python_exec, "router_app.py"], env=env)
    processes.append(p_router)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down all services...")
        for p in processes:
            p.terminate()

if __name__ == "__main__":
    start_services()
