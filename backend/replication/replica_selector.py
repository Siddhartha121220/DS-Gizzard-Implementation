"""
Replica Selector Module
Selects the replica node for a given primary node in the consistent hash ring.
Replication factor = 2 (primary + 1 replica)
"""


class ReplicaSelector:
    """Selects replica nodes based on consistent hash ring topology."""

    def __init__(self, hash_ring):
        """
        Initialize replica selector with hash ring.
        
        Args:
            hash_ring: ConsistentHashRing instance with get_ring_state() method
        """
        self.hash_ring = hash_ring
        self.ring_state = hash_ring.get_ring_state()
        self.nodes = self.ring_state.get('nodes', [])
        self.build_node_index()

    def build_node_index(self):
        """Build a mapping of physical nodes for quick lookup."""
        # Create a list of unique physical nodes (not virtual nodes)
        self.physical_nodes = []
        seen = set()
        for node in self.nodes:
            if node not in seen:
                self.physical_nodes.append(node)
                seen.add(node)

    def get_replica_node(self, primary_node):
        """
        Get the replica node for a given primary node.
        Replica is the next physical node clockwise in the hash ring.
        
        Args:
            primary_node: The primary shard name (e.g., "Shard1")
            
        Returns:
            The replica shard name (e.g., "Shard2"), or None if not enough nodes
        """
        if len(self.physical_nodes) < 2:
            # Cannot replicate with only 1 node
            return None

        try:
            primary_index = self.physical_nodes.index(primary_node)
            replica_index = (primary_index + 1) % len(self.physical_nodes)
            return self.physical_nodes[replica_index]
        except ValueError:
            # Primary node not found
            return None

    def get_replica_nodes(self, primary_node, replication_factor=2):
        """
        Get multiple replica nodes (for future scalability).
        
        Args:
            primary_node: The primary shard name
            replication_factor: Number of total copies (including primary)
            
        Returns:
            List of replica shard names (excludes primary)
        """
        replicas = []
        if len(self.physical_nodes) < replication_factor:
            return replicas

        try:
            primary_index = self.physical_nodes.index(primary_node)
            for i in range(1, replication_factor):
                replica_index = (primary_index + i) % len(self.physical_nodes)
                replicas.append(self.physical_nodes[replica_index])
            return replicas
        except ValueError:
            return []

    def get_full_replica_set(self, primary_node):
        """
        Get the complete replica set for a primary node.
        
        Returns:
            Dict with 'primary' and 'replicas' keys
        """
        replicas = self.get_replica_nodes(primary_node, replication_factor=2)
        return {
            'primary': primary_node,
            'replicas': replicas,
            'replication_factor': 1 + len(replicas)
        }
