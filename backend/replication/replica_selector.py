"""
Replica Selector Module
Selects the replica node for a given primary node in the consistent hash ring.
Replication factor = 2 (primary + 1 replica)
"""


class ReplicaSelector:
    """Selects replica nodes based on host-aware ring topology."""

    def __init__(self, hash_ring, shard_lookup):
        """
        Initialize replica selector with hash ring and shard lookup.
        
        Args:
            hash_ring: ConsistentHashRing instance
            shard_lookup: Dict mapping shard names to {host, port, server}
        """
        self.hash_ring = hash_ring
        self.shard_lookup = shard_lookup
        self.ring_state = hash_ring.get_ring_state()
        self.nodes = self.ring_state.get('nodes', [])
        # Ordered list of physical shard names
        self.physical_nodes = self.nodes
        self.ring_order = self.nodes

    def _get_node_host(self, shard_name):
        """Get the host (IP/Server) for a given shard."""
        shard_info = self.shard_lookup.get(shard_name, {})
        return shard_info.get('host') or shard_info.get('server')

    def get_replica_node(self, primary_node):
        """
        Get the replica node for a given primary node.
        Replica is the first node clockwise that is on a DIFFERENT host.
        
        Args:
            primary_node: The primary shard name (e.g., "Shard1")
            
        Returns:
            The replica shard name, or None if no suitable replica found
        """
        primary_host = self._get_node_host(primary_node)
        if not primary_host:
            return None

        try:
            start_index = self.ring_order.index(primary_node)
            ring_size = len(self.ring_order)
            
            # Search clockwise for a node on a different host
            for i in range(1, ring_size):
                candidate_index = (start_index + i) % ring_size
                candidate_node = self.ring_order[candidate_index]
                candidate_host = self._get_node_host(candidate_node)
                
                if candidate_host and candidate_host != primary_host:
                    return candidate_node
            
            return None
        except ValueError:
            return None

    def get_replica_nodes(self, primary_node, replication_factor=2):
        """
        Get multiple replica nodes on distinct hosts.
        
        Args:
            primary_node: The primary shard name
            replication_factor: Number of total copies (including primary)
            
        Returns:
            List of replica shard names (excludes primary)
        """
        replicas = []
        primary_host = self._get_node_host(primary_node)
        if not primary_host:
            return replicas

        used_hosts = {primary_host}
        
        try:
            start_index = self.ring_order.index(primary_node)
            ring_size = len(self.ring_order)
            
            for i in range(1, ring_size):
                if len(replicas) >= replication_factor - 1:
                    break
                    
                candidate_index = (start_index + i) % ring_size
                candidate_node = self.ring_order[candidate_index]
                candidate_host = self._get_node_host(candidate_node)
                
                if candidate_host and candidate_host not in used_hosts:
                    replicas.append(candidate_node)
                    used_hosts.add(candidate_host)
            
            return replicas
        except ValueError:
            return []

    def get_full_replica_set(self, primary_node):
        """
        Get the complete replica set for a primary node.
        """
        replicas = self.get_replica_nodes(primary_node, replication_factor=2)
        return {
            'primary': primary_node,
            'replicas': replicas,
            'replication_factor': 1 + len(replicas)
        }
