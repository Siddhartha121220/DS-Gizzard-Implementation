"""
Failover Manager Module
Handles read/write failures with retry mechanism and automatic failover to replicas.
"""
import logging
import json
import sys
sys.path.append('gen-py')

from thrift.transport import TSocket, TTransport
from thrift.protocol import TBinaryProtocol
from router_service import TweetService


class FailoverManager:
    """Manages failover logic for read and write operations."""
    
    def __init__(self, shard_lookup, node_registry, event_logger, replication_manager, config):
        """
        Initialize failover manager.
        
        Args:
            shard_lookup: Dict mapping shard names to {host, port, server} info
            node_registry: NodeRegistry instance
            event_logger: EventLogger instance
            replication_manager: ReplicationManager instance
            config: FailoverConfig instance
        """
        self.shard_lookup = shard_lookup
        self.node_registry = node_registry
        self.event_logger = event_logger
        self.replication_manager = replication_manager
        self.config = config
    
    def handle_read_failure(self, tweet_id, primary_node, exception):
        """
        Handle read failure with retry and failover logic.
        
        Steps:
        1. Retry primary once
        2. If retry fails, failover to replica
        
        Args:
            tweet_id: Tweet ID to read
            primary_node: Primary shard name
            exception: Original exception
            
        Returns:
            Dict with success status, data, node_used, and failover flag
        """
        logging.warning(f"[Failover] Read failure on {primary_node} for tweet {tweet_id}: {exception}")
        
        # Get replica node
        replica_node = self.replication_manager.replica_selector.get_replica_node(primary_node)
        if not replica_node:
            self.event_logger.log_event(
                "failover", tweet_id, primary_node, None, "read_failed_no_replica",
                f"No replica available for {primary_node}"
            )
            return {
                "success": False,
                "data": None,
                "node_used": primary_node,
                "failover": False,
                "error": "No replica available"
            }
        
        # Retry primary once
        logging.info(f"[Failover] Retrying read on {primary_node}")
        try:
            data = self._attempt_read(tweet_id, primary_node, self.config.REQUEST_TIMEOUT)
            logging.info(f"[Failover] Retry successful on {primary_node}")
            return {
                "success": True,
                "data": data,
                "node_used": primary_node,
                "failover": False
            }
        except Exception as retry_exception:
            logging.warning(f"[Failover] Retry failed on {primary_node}: {retry_exception}")
        
        # Failover to replica
        logging.info(f"[Failover] Failing over read to replica {replica_node}")
        try:
            data = self._attempt_read(tweet_id, replica_node, self.config.REQUEST_TIMEOUT)
            logging.info(f"[Failover] Read successful on replica {replica_node}")
            
            self.event_logger.log_event(
                "failover", tweet_id, primary_node, replica_node, "read_failover",
                f"Read redirected from {primary_node} to {replica_node}"
            )
            
            return {
                "success": True,
                "data": data,
                "node_used": replica_node,
                "failover": True
            }
        except Exception as failover_exception:
            logging.error(f"[Failover] Failover read failed on {replica_node}: {failover_exception}")
            
            self.event_logger.log_event(
                "failover", tweet_id, primary_node, replica_node, "read_failover_failed",
                f"Both primary and replica failed"
            )
            
            return {
                "success": False,
                "data": None,
                "node_used": replica_node,
                "failover": True,
                "error": str(failover_exception)
            }
    
    def handle_write_failure(self, tweet_id, user_id, text, primary_node, exception):
        """
        Handle write failure by writing to replica.
        
        Args:
            tweet_id: Tweet ID
            user_id: User ID
            text: Tweet text
            primary_node: Primary shard name
            exception: Original exception
            
        Returns:
            Dict with success status, node_used, and failover flag
        """
        logging.warning(f"[Failover] Write failure on {primary_node} for tweet {tweet_id}: {exception}")
        
        # Get replica node
        replica_node = self.replication_manager.replica_selector.get_replica_node(primary_node)
        if not replica_node:
            self.event_logger.log_event(
                "failover", tweet_id, primary_node, None, "write_failed_no_replica",
                f"No replica available for {primary_node}"
            )
            return {
                "success": False,
                "node_used": primary_node,
                "failover": False,
                "error": "No replica available"
            }
        
        # Write to replica
        logging.info(f"[Failover] Writing to replica {replica_node}")
        try:
            success = self._attempt_write(tweet_id, user_id, text, replica_node, self.config.REQUEST_TIMEOUT)
            logging.info(f"[Failover] Write successful on replica {replica_node}")
            
            self.event_logger.log_event(
                "failover", tweet_id, primary_node, replica_node, "write_failover",
                f"Write redirected from {primary_node} to {replica_node}"
            )
            
            return {
                "success": True,
                "node_used": replica_node,
                "failover": True
            }
        except Exception as failover_exception:
            logging.error(f"[Failover] Failover write failed on {replica_node}: {failover_exception}")
            
            self.event_logger.log_event(
                "failover", tweet_id, primary_node, replica_node, "write_failover_failed",
                f"Write failed on both primary and replica"
            )
            
            return {
                "success": False,
                "node_used": replica_node,
                "failover": True,
                "error": str(failover_exception)
            }
    
    def _attempt_read(self, tweet_id, shard_name, timeout):
        """
        Attempt to read from a specific shard.
        
        Args:
            tweet_id: Tweet ID to read
            shard_name: Shard name
            timeout: Timeout in seconds
            
        Returns:
            Parsed tweet data
            
        Raises:
            Exception if read fails
        """
        client, transport = self._get_thrift_client(shard_name, timeout)
        if not client:
            raise Exception(f"Cannot create client for {shard_name}")
        
        try:
            transport.open()
            tweet_data_str = client.getTweet(tweet_id)
            transport.close()
            
            if not tweet_data_str:
                raise Exception("Tweet not found")
            
            return json.loads(tweet_data_str)
        except Exception as e:
            if transport.isOpen():
                transport.close()
            raise e
    
    def _attempt_write(self, tweet_id, user_id, text, shard_name, timeout):
        """
        Attempt to write to a specific shard.
        
        Args:
            tweet_id: Tweet ID
            user_id: User ID
            text: Tweet text
            shard_name: Shard name
            timeout: Timeout in seconds
            
        Returns:
            True if successful
            
        Raises:
            Exception if write fails
        """
        client, transport = self._get_thrift_client(shard_name, timeout)
        if not client:
            raise Exception(f"Cannot create client for {shard_name}")
        
        try:
            transport.open()
            success = client.storeTweet(tweet_id, user_id, text)
            transport.close()
            return success
        except Exception as e:
            if transport.isOpen():
                transport.close()
            raise e
    
    def _get_thrift_client(self, shard_name, timeout):
        """
        Create Thrift client with timeout.
        
        Args:
            shard_name: Shard name
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (client, transport) or (None, None) if shard not found
        """
        shard_conf = self.shard_lookup.get(shard_name)
        if not shard_conf:
            return None, None
        
        transport = TSocket.TSocket(shard_conf['host'], shard_conf['port'])
        transport.setTimeout(timeout * 1000)  # milliseconds
        transport = TTransport.TBufferedTransport(transport)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        client = TweetService.Client(protocol)
        
        return client, transport
