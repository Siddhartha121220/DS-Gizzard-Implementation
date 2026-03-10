import subprocess
import time
import sys
import json
import os
import shutil

def find_thrift_compiler():
    # Allow override via THRIFT_BIN, otherwise look for local thrift.exe or PATH thrift.
    env_bin = os.environ.get("THRIFT_BIN")
    if env_bin:
        return env_bin
    # Only use the bundled thrift.exe on Windows.
    if os.name == "nt":
        local_thrift = os.path.join(os.path.dirname(__file__), "thrift.exe")
        if os.path.exists(local_thrift):
            return local_thrift
    return shutil.which("thrift")

def generate_thrift():
    thrift_bin = find_thrift_compiler()
    if not thrift_bin:
        print("Thrift compiler not found. Skipping codegen (set THRIFT_BIN or add thrift to PATH).")
        return

    print("Generating Thrift Python bindings...")
    result = subprocess.run(
        [thrift_bin, "--gen", "py", "tweet.thrift"],
        cwd=os.path.dirname(__file__),
    )
    if result.returncode != 0:
        print("Thrift code generation failed. Aborting startup.")
        sys.exit(result.returncode)

def start_services():
    processes = []

    # Always regenerate thrift bindings when compiler is available.
    generate_thrift()
    
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
