import socket
import json
import os

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Connect to an external IP to route through the default interface
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def main():
    print("=========================================")
    print("   Gizzard Cluster Setup Automation     ")
    print("=========================================")
    
    laptop1_ip = get_local_ip()
    print(f"\n[Detected] Laptop 1 (Router/Frontend) IP: {laptop1_ip}")
    print("Make sure this is the IP assigned by the Wi-Fi Hotspot.\n")
    
    laptop2_ip = input("Enter Laptop 2 IP (or press Enter for 127.0.0.1): ").strip() or "127.0.0.1"
    laptop3_ip = input("Enter Laptop 3 IP (or press Enter for 127.0.0.1): ").strip() or "127.0.0.1"
    
    config = {
        "servers": {
            "Laptop1": {
                "shards": {
                    "Shard1": {"host": laptop1_ip, "port": 9091},
                    "Shard2": {"host": laptop1_ip, "port": 9092}
                }
            },
            "Laptop2": {
                "shards": {
                    "Shard3": {"host": laptop2_ip, "port": 9093},
                    "Shard4": {"host": laptop2_ip, "port": 9094}
                }
            },
            "Laptop3": {
                "shards": {
                    "Shard5": {"host": laptop3_ip, "port": 9095},
                    "Shard6": {"host": laptop3_ip, "port": 9096}
                }
            }
        }
    }
    
    config_path = os.path.join("config", "nodes_config.json")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)
        
    print(f"\n[Success] Configuration saved to {config_path}!")
    
    print("\n=================")
    print("   Next Steps")
    print("=================")
    print("1. On Laptop 1 (Router):")
    print("   Run `python run_all.py` (in backend) and `npm run dev -- --host` (in frontend).")
    print("   Access the dashboard at http://" + laptop1_ip + ":5173\n")
    
    print(f"2. On Laptop 2 ({laptop2_ip}):")
    print("   Run `python storage_node.py --name Shard3 --port 9093`")
    print("   Run `python storage_node.py --name Shard4 --port 9094`\n")
    
    print(f"3. On Laptop 3 ({laptop3_ip}):")
    print("   Run `python storage_node.py --name Shard5 --port 9095`")
    print("   Run `python storage_node.py --name Shard6 --port 9096`\n")

if __name__ == "__main__":
    main()
