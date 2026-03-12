namespace py router_service

service TweetService {
    bool storeTweet(1: string tweet_id, 2: string user_id, 3: string text, 4: bool is_replica),
    string getTweet(1: string tweet_id),
    string getAllTweets(),
    string heartbeat()
}
