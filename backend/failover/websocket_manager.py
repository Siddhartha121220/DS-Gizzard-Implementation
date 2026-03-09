"""
WebSocket Manager Module
Manages real-time event broadcasting to frontend clients.
"""


class WebSocketManager:
    """Manages WebSocket event emissions for real-time updates."""
    
    def __init__(self, socketio):
        """
        Initialize WebSocket manager.
        
        Args:
            socketio: Flask-SocketIO instance
        """
        self.socketio = socketio
    
    def emit_node_status_update(self, shard_name, status, health_info):
        """
        Broadcast node status update to all connected clients.
        
        Args:
            shard_name: Name of the shard
            status: Node status (ACTIVE/DOWN/RECOVERING)
            health_info: Detailed health information
        """
        self.socketio.emit('node_status_update', {
            "shard_name": shard_name,
            "status": status,
            "health_info": health_info
        })
    
    def emit_failover_event(self, event_data):
        """
        Broadcast failover event to all connected clients.
        
        Args:
            event_data: Failover event dictionary
        """
        self.socketio.emit('failover_event', event_data)
    
    def emit_all_node_status(self, all_status):
        """
        Broadcast complete node status to all connected clients.
        
        Args:
            all_status: Dictionary of all node statuses
        """
        self.socketio.emit('all_node_status', all_status)
