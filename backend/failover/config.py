"""
Failover Configuration Module
Centralized configuration for failover and fault tolerance system.
"""


class FailoverConfig:
    """Configuration constants for failover system."""
    
    # Health monitoring settings
    HEARTBEAT_INTERVAL = 5  # seconds between health checks
    HEARTBEAT_TIMEOUT = 2   # seconds to wait for heartbeat response
    
    # Recovery settings
    RECOVERY_THRESHOLD = 3  # consecutive successful heartbeats needed for recovery
    
    # Retry settings
    MAX_RETRY_ATTEMPTS = 1  # number of retries before failover
    REQUEST_TIMEOUT = 2     # seconds for read/write request timeout
    
    # Logging settings
    FAILOVER_LOG_FILE = "logs/failover_events.log"
    MAX_MEMORY_EVENTS = 100  # max events kept in memory
