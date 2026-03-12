import sys
import os
import json

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from replication.replica_selector import ReplicaSelector

class MockHashRing:
    def __init__(self, nodes):
        self.nodes = nodes
    def get_ring_state(self):
        return {'nodes': self.nodes}

def test_replica_selection():
    # Setup mock data
    nodes = ["Shard1", "Shard2", "Shard3", "Shard4", "Shard5", "Shard6"]
    shard_lookup = {
        "Shard1": {"host": "10.0.0.1"},
        "Shard2": {"host": "10.0.0.1"},
        "Shard3": {"host": "10.0.0.2"},
        "Shard4": {"host": "10.0.0.2"},
        "Shard5": {"host": "10.0.0.3"},
        "Shard6": {"host": "10.0.0.3"},
    }
    
    hash_ring = MockHashRing(nodes)
    selector = ReplicaSelector(hash_ring, shard_lookup)
    
    print("Testing Host-Aware Replication:")
    print("-" * 30)
    
    for shard in nodes:
        replica = selector.get_replica_node(shard)
        primary_host = shard_lookup[shard]["host"]
        replica_host = shard_lookup[replica]["host"] if replica else "None"
        
        status = "PASSED" if primary_host != replica_host else "FAILED"
        print(f"Primary: {shard} ({primary_host}) -> Replica: {replica} ({replica_host}) | {status}")

if __name__ == "__main__":
    test_replica_selection()
