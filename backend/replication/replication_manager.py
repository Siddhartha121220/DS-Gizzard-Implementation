"""
Replication Manager Module
Handles replication of tweets across multiple nodes.
"""

import json
from datetime import datetime
from thrift.transport import TSocket, TTransport
from thrift.protocol import TBinaryProtocol
from router_service import TweetService
from .replica_selector import ReplicaSelector


class ReplicationManager:
    """Manages tweet replication across storage nodes."""

    def __init__(self, hash_ring, shard_lookup):
        """
        Initialize replication manager.
        
        Args:
            hash_ring: ConsistentHashRing instance
            shard_lookup: Dict mapping shard names to {host, port} info
        """
        self.hash_ring = hash_ring
        self.shard_lookup = shard_lookup
        self.replica_selector = ReplicaSelector(hash_ring)
        # Track replication metadata
        self.replication_map = {}
        self.replica_data = {}

    def replicate_write(self, tweet_id, user_id, text, primary_node):
        """
        Replicate a tweet write across primary and replica nodes.
        
        Steps:
        1. Store tweet on primary node (assumed already done)
        2. Get replica node from replica selector
        3. Send replication request to replica node
        
        Args:
            tweet_id: Unique tweet identifier
            user_id: Tweet author ID
            text: Tweet content
            primary_node: Primary shard name (e.g., "Shard1")
            
        Returns:
            Dict with replication status:
            {
                'tweet_id': tweet_id,
                'primary_node': primary_node,
                'replica_node': replica_node,
                'status': 'success' or 'failed',
                'message': status message
            }
        """
        # Get replica node
        replica_node = self.replica_selector.get_replica_node(primary_node)
        
        if not replica_node:
            return {
                'tweet_id': tweet_id,
                'primary_node': primary_node,
                'replica_node': None,
                'status': 'failed',
                'message': 'Could not determine replica node'
            }

        # Store replication metadata
        replication_info = {
            'tweet_id': tweet_id,
            'primary_node': primary_node,
            'replica_node': replica_node,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending'
        }
        self.replication_map[tweet_id] = replication_info

        # Send replication request to replica node
        try:
            success = self._send_replica_write(
                tweet_id, user_id, text, replica_node
            )
            
            if success:
                replication_info['status'] = 'success'
                self.replica_data[tweet_id] = {
                    'user_id': user_id,
                    'text': text,
                    'primary_node': primary_node,
                    'replica_node': replica_node,
                    'timestamp': replication_info['timestamp']
                }
                return {
                    'tweet_id': tweet_id,
                    'primary_node': primary_node,
                    'replica_node': replica_node,
                    'status': 'success',
                    'message': f'Tweet replicated to {replica_node}'
                }
            else:
                replication_info['status'] = 'failed'
                return {
                    'tweet_id': tweet_id,
                    'primary_node': primary_node,
                    'replica_node': replica_node,
                    'status': 'failed',
                    'message': f'Failed to replicate to {replica_node}'
                }
        except Exception as e:
            replication_info['status'] = 'failed'
            return {
                'tweet_id': tweet_id,
                'primary_node': primary_node,
                'replica_node': replica_node,
                'status': 'failed',
                'message': f'Replication error: {str(e)}'
            }

    def _send_replica_write(self, tweet_id, user_id, text, replica_node):
        """
        Send actual replication write to replica node via Thrift.
        
        Args:
            tweet_id: Tweet ID
            user_id: User ID
            text: Tweet text
            replica_node: Replica shard name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if replica_node not in self.shard_lookup:
                return False

            shard_info = self.shard_lookup[replica_node]
            host = shard_info.get('host', 'localhost')
            port = shard_info.get('port', 9091)

            # Create Thrift connection
            transport = TSocket.TSocket(host, port)
            transport = TTransport.TBufferedTransport(transport)
            protocol = TBinaryProtocol.TBinaryProtocol(transport)
            client = TweetService.Client(protocol)

            transport.open()
            try:
                # Call storeTweet with is_replica flag
                result = client.storeTweet(tweet_id, user_id, text)
                transport.close()
                return result
            except Exception as e:
                transport.close()
                return False

        except Exception as e:
            return False

    def get_replication_status(self, tweet_id):
        """
        Get replication status for a specific tweet.
        
        Args:
            tweet_id: Tweet ID to check
            
        Returns:
            Replication metadata or None if not found
        """
        return self.replication_map.get(tweet_id)

    def get_replication_map(self):
        """
        Get the mapping of all replicated tweets.
        
        Returns:
            List of replication records
        """
        return list(self.replication_map.values())

    def get_replication_stats(self):
        """
        Get replication statistics.
        
        Returns:
            Dict with stats:
            {
                'total_tweets': N,
                'successful_replications': M,
                'failed_replications': K,
                'nodes': {...}
            }
        """
        total = len(self.replication_map)
        successful = sum(
            1 for r in self.replication_map.values()
            if r['status'] == 'success'
        )
        failed = total - successful

        # Count tweets per node
        node_stats = {}
        for info in self.replication_map.values():
            primary = info['primary_node']
            replica = info['replica_node']
            
            if primary not in node_stats:
                node_stats[primary] = {'primary': 0, 'replica': 0}
            if replica not in node_stats:
                node_stats[replica] = {'primary': 0, 'replica': 0}
            
            node_stats[primary]['primary'] += 1
            node_stats[replica]['replica'] += 1

        return {
            'total_tweets': total,
            'successful_replications': successful,
            'failed_replications': failed,
            'by_node': node_stats
        }
