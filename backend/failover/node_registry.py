"""
Node Registry Module
Thread-safe registry for tracking node health status and recovery progress.
"""
import threading
from datetime import datetime
from enum import Enum


class NodeStatus(Enum):
    """Node health status states."""
    ACTIVE = "ACTIVE"
    DOWN = "DOWN"
    RECOVERING = "RECOVERING"


class NodeRegistry:
    """Thread-safe registry for node status tracking with gradual recovery logic."""
    
    def __init__(self, recovery_threshold=3):
        """
        Initialize node registry.
        
        Args:
            recovery_threshold: Number of consecutive successful heartbeats needed for recovery
        """
        self.node_status = {}
        self.consecutive_successes = {}
        self.last_heartbeat = {}
        self.recovery_threshold = recovery_threshold
        self.lock = threading.Lock()
    
    def initialize_node(self, shard_name):
        """Initialize a node with ACTIVE status."""
        with self.lock:
            self.node_status[shard_name] = NodeStatus.ACTIVE
            self.consecutive_successes[shard_name] = 0
            self.last_heartbeat[shard_name] = datetime.now()
    
    def record_success(self, shard_name):
        """
        Record successful heartbeat and update status.
        Implements gradual recovery: DOWN -> RECOVERING -> ACTIVE
        """
        with self.lock:
            if shard_name not in self.node_status:
                self.initialize_node(shard_name)
                return
            
            current_status = self.node_status[shard_name]
            self.last_heartbeat[shard_name] = datetime.now()
            
            if current_status == NodeStatus.ACTIVE:
                self.consecutive_successes[shard_name] = 0
            elif current_status == NodeStatus.DOWN:
                self.consecutive_successes[shard_name] += 1
                if self.consecutive_successes[shard_name] >= self.recovery_threshold:
                    self.node_status[shard_name] = NodeStatus.ACTIVE
                    self.consecutive_successes[shard_name] = 0
                else:
                    self.node_status[shard_name] = NodeStatus.RECOVERING
            elif current_status == NodeStatus.RECOVERING:
                self.consecutive_successes[shard_name] += 1
                if self.consecutive_successes[shard_name] >= self.recovery_threshold:
                    self.node_status[shard_name] = NodeStatus.ACTIVE
                    self.consecutive_successes[shard_name] = 0
    
    def record_failure(self, shard_name):
        """Record failed heartbeat and mark node as DOWN."""
        with self.lock:
            if shard_name not in self.node_status:
                self.initialize_node(shard_name)
            
            self.node_status[shard_name] = NodeStatus.DOWN
            self.consecutive_successes[shard_name] = 0
    
    def get_status(self, shard_name):
        """Get current status of a node."""
        with self.lock:
            return self.node_status.get(shard_name, NodeStatus.DOWN)
    
    def get_all_status(self):
        """Get status of all nodes."""
        with self.lock:
            return {shard: status.value for shard, status in self.node_status.items()}
    
    def get_health_info(self, shard_name):
        """Get detailed health info for a node."""
        with self.lock:
            if shard_name not in self.node_status:
                return None
            
            return {
                "shard_name": shard_name,
                "status": self.node_status[shard_name].value,
                "last_heartbeat": self.last_heartbeat[shard_name].isoformat(),
                "consecutive_successes": self.consecutive_successes[shard_name]
            }
    
    def get_all_health_info(self):
        """Get detailed health info for all nodes."""
        with self.lock:
            return {
                shard: {
                    "status": self.node_status[shard].value,
                    "last_heartbeat": self.last_heartbeat[shard].isoformat(),
                    "consecutive_successes": self.consecutive_successes[shard]
                }
                for shard in self.node_status.keys()
            }
