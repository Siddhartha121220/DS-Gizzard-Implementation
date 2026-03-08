import hashlib
import bisect

class ConsistentHashRing:
    def __init__(self, replicas=3):
        self.replicas = replicas
        self.ring = {}
        self.sorted_keys = []
        self.nodes = set()

    def _hash(self, key):
        return int(hashlib.sha256(key.encode('utf-8')).hexdigest(), 16)

    def add_node(self, node):
        self.nodes.add(node)
        for i in range(self.replicas):
            virtual_node_key = f"{node}:{i}"
            key = self._hash(virtual_node_key)
            self.ring[key] = node
            bisect.insort(self.sorted_keys, key)

    def remove_node(self, node):
        if node in self.nodes:
            self.nodes.remove(node)
            for i in range(self.replicas):
                virtual_node_key = f"{node}:{i}"
                key = self._hash(virtual_node_key)
                if key in self.ring:
                    del self.ring[key]
                    self.sorted_keys.remove(key)

    def get_node(self, key):
        if not self.ring:
            return None
        hash_val = self._hash(str(key))
        
        # Binary search for the first node with a key >= hash_val
        idx = bisect.bisect_right(self.sorted_keys, hash_val)
        
        # If we reached the end of the ring, wrap around to the first node
        if idx == len(self.sorted_keys):
            idx = 0
            
        return self.ring[self.sorted_keys[idx]]

    def get_ring_state(self):
        """Return a mapping of ring keys to their assigned nodes."""
        return {
            "ring": [{"hash": str(k), "node": self.ring[k]} for k in self.sorted_keys],
            "nodes": list(self.nodes)
        }
