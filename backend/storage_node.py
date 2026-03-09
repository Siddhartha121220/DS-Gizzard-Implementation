import sys
import argparse
import logging
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

# Import generated thrift files
sys.path.append('gen-py')
from router_service import TweetService
from router_service.ttypes import *

logging.basicConfig(level=logging.INFO)

class TweetServiceHandler:
    def __init__(self, node_id):
        self.node_id = node_id
        self.tweets = {}
        self.replicas = set()  # Track which tweets are replicas
        logging.info(f"Initialized Storage Node: {self.node_id}")

    def storeTweet(self, tweet_id, user_id, text, is_replica=False):
        """
        Store a tweet on this node.
        
        Args:
            tweet_id: Unique tweet ID
            user_id: User ID
            text: Tweet text
            is_replica: Boolean flag indicating if this is a replica copy
        """
        logging.info(
            f"[{self.node_id}] Storing tweet ID {tweet_id} from User {user_id}"
            f" (replica={is_replica})"
        )
        self.tweets[tweet_id] = {
            "tweet_id": tweet_id,
            "user_id": user_id,
            "text": text,
            "stored_on": self.node_id,
            "is_replica": is_replica
        }
        if is_replica:
            self.replicas.add(tweet_id)
        return True

    def getTweet(self, tweet_id):
        logging.info(f"[{self.node_id}] Fetching tweet ID {tweet_id}")
        if tweet_id in self.tweets:
            # For simplicity, returning a JSON-like string
            import json
            return json.dumps(self.tweets[tweet_id])
        return ""

    def getAllTweets(self):
        logging.info(f"[{self.node_id}] Fetching all tweets")
        import json
        return json.dumps(list(self.tweets.values()))

    def heartbeat(self):
        """
        Health check endpoint that returns node status.
        
        Returns:
            JSON string with status, timestamp, and node_id
        """
        import json
        from datetime import datetime
        return json.dumps({
            "status": "alive",
            "timestamp": datetime.now().isoformat(),
            "node_id": self.node_id
        })

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True, help="Port to listen on")
    parser.add_argument("--name", type=str, required=True, help="Node name (e.g., Node1)")
    args = parser.parse_args()

    handler = TweetServiceHandler(args.name)
    processor = TweetService.Processor(handler)
    transport = TSocket.TServerSocket(host='127.0.0.1', port=args.port)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()

    server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
    
    logging.info(f"Starting {args.name} on port {args.port}...")
    server.serve()
    logging.info("Done.")
