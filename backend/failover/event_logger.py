"""
Event Logger Module
Hybrid logging system with in-memory storage and persistent file logging.
"""
import threading
import json
import os
from datetime import datetime
from collections import deque


class EventLogger:
    """Hybrid event logger with memory and file storage."""
    
    def __init__(self, log_file_path, max_memory_events=100):
        """
        Initialize event logger.
        
        Args:
            log_file_path: Path to persistent log file
            max_memory_events: Maximum events to keep in memory
        """
        self.log_file = log_file_path
        self.max_memory_events = max_memory_events
        self.memory_events = deque(maxlen=max_memory_events)
        self.lock = threading.Lock()
        
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    def log_event(self, event_type, tweet_id, primary_node, replica_node, action, details=None):
        """
        Log a failover event to both memory and file.
        
        Args:
            event_type: Type of event (e.g., "failover", "recovery", "health_check")
            tweet_id: Tweet ID involved (or None)
            primary_node: Primary node name
            replica_node: Replica node name (or None)
            action: Action taken (e.g., "read_failover", "write_failover", "node_down", "node_up")
            details: Optional additional details
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "tweet_id": tweet_id,
            "primary_node": primary_node,
            "replica_node": replica_node,
            "action": action,
            "details": details
        }
        
        with self.lock:
            # Add to memory
            self.memory_events.append(event)
            
            # Append to file
            try:
                with open(self.log_file, 'a') as f:
                    f.write(json.dumps(event) + '\n')
            except Exception as e:
                # Log to stderr if file write fails
                import sys
                print(f"Failed to write to log file: {e}", file=sys.stderr)
    
    def get_recent_events(self, limit=50):
        """
        Get recent events from memory.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of recent events (most recent first)
        """
        with self.lock:
            events = list(self.memory_events)
            events.reverse()  # Most recent first
            return events[:limit]
    
    def get_all_events(self):
        """
        Get all events from memory.
        
        Returns:
            List of all events in memory (most recent first)
        """
        with self.lock:
            events = list(self.memory_events)
            events.reverse()
            return events
    
    def clear_memory(self):
        """Clear in-memory events (keeps file intact)."""
        with self.lock:
            self.memory_events.clear()
