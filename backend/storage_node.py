import sys
import os
import sqlite3
import argparse
import logging
import json
from datetime import datetime
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

        # --- SQLite setup ---
        # Store DB files in a local `data/` folder next to this script.
        # Each shard gets its own file (e.g. data/Shard5.db).
        # The data/ folder is git-ignored, so every teammate's machine
        # maintains its own independent local database.
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(data_dir, exist_ok=True)
        db_path = os.path.join(data_dir, f"{node_id}.db")

        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()
        self._load_from_db()

        logging.info(f"Initialized Storage Node: {self.node_id} | DB: {db_path}")

    def _init_db(self):
        """Create the tweets table if it doesn't already exist."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tweets (
                tweet_id  TEXT PRIMARY KEY,
                user_id   TEXT NOT NULL,
                text      TEXT NOT NULL,
                stored_on TEXT NOT NULL,
                is_replica INTEGER NOT NULL DEFAULT 0
            )
        """)
        self.conn.commit()

    def _load_from_db(self):
        """Load all previously stored tweets from SQLite into memory on startup."""
        cursor = self.conn.execute(
            "SELECT tweet_id, user_id, text, stored_on, is_replica FROM tweets"
        )
        for row in cursor.fetchall():
            tweet_id, user_id, text, stored_on, is_replica = row
            self.tweets[tweet_id] = {
                "tweet_id": tweet_id,
                "user_id": user_id,
                "text": text,
                "stored_on": stored_on,
                "is_replica": bool(is_replica)
            }
            if is_replica:
                self.replicas.add(tweet_id)
        logging.info(f"[{self.node_id}] Loaded {len(self.tweets)} tweet(s) from disk.")

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

        # Persist to SQLite (INSERT OR REPLACE handles duplicates gracefully)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO tweets (tweet_id, user_id, text, stored_on, is_replica)
            VALUES (?, ?, ?, ?, ?)
            """,
            (tweet_id, user_id, text, self.node_id, int(is_replica))
        )
        self.conn.commit()

        return True

    def getTweet(self, tweet_id):
        logging.info(f"[{self.node_id}] Fetching tweet ID {tweet_id}")
        if tweet_id in self.tweets:
            return json.dumps(self.tweets[tweet_id])
        return ""

    def getAllTweets(self):
        logging.info(f"[{self.node_id}] Fetching all tweets")
        return json.dumps(list(self.tweets.values()))

    def heartbeat(self):
        """
        Health check endpoint that returns node status.

        Returns:
            JSON string with status, timestamp, and node_id
        """
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
    transport = TSocket.TServerSocket(host='0.0.0.0', port=args.port)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()

    server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)

    logging.info(f"Starting {args.name} on port {args.port}...")
    server.serve()
    logging.info("Done.")
