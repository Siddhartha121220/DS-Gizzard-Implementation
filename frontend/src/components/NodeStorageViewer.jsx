import { useEffect, useState } from 'react';
import './NodeStorageViewer.css';

export default function NodeStorageViewer() {
  const [nodes, setNodes] = useState([]);
  const [selectedNode, setSelectedNode] = useState('');
  const [tweets, setTweets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [allShards, setAllShards] = useState({});
  const [filter, setFilter] = useState('all'); // 'all', 'primary', 'replica'

  // Fetch available nodes on mount
  useEffect(() => {
    const fetchNodes = async () => {
      try {
        const response = await fetch('http://localhost:5000/hash-ring');
        if (!response.ok) throw new Error('Failed to fetch nodes');
        
        const data = await response.json();
        const uniqueNodes = [...new Set(data.nodes.map(n => n.shard))];
        setNodes(uniqueNodes);
        if (uniqueNodes.length > 0 && !selectedNode) {
          setSelectedNode(uniqueNodes[0]);
        }
      } catch (err) {
        console.error('Error fetching nodes:', err);
        setError(err.message);
      }
    };

    fetchNodes();
  }, [selectedNode]);

  // Fetch tweets for selected node
  useEffect(() => {
    const fetchTweets = async () => {
      if (!selectedNode) return;

      try {
        setLoading(true);
        setError(null);
        
        const response = await fetch('http://localhost:5000/shards');
        if (!response.ok) throw new Error('Failed to fetch shards');
        
        const data = await response.json();
        setAllShards(data);
        
        if (data[selectedNode] && data[selectedNode].tweets) {
          setTweets(data[selectedNode].tweets);
        } else {
          setTweets([]);
        }
      } catch (err) {
        console.error('Error fetching tweets:', err);
        setError(err.message);
        setTweets([]);
      } finally {
        setLoading(false);
      }
    };

    fetchTweets();
    const interval = setInterval(fetchTweets, 3000);
    return () => clearInterval(interval);
  }, [selectedNode]);

  const getFilteredTweets = () => {
    if (filter === 'all') return tweets;
    if (filter === 'primary') return tweets.filter(t => !t.is_replica);
    if (filter === 'replica') return tweets.filter(t => t.is_replica);
    return tweets;
  };

  const filteredTweets = getFilteredTweets();

  return (
    <div className="node-storage-viewer bg-white rounded-lg shadow-sm p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Node Storage Viewer</h2>
        <p className="text-gray-600">
          Select a node and view all tweets stored on it
        </p>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded text-red-700">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        {/* Node Selector */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Select Node
          </label>
          <select
            value={selectedNode}
            onChange={(e) => setSelectedNode(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
          >
            {nodes.map(node => (
              <option key={node} value={node}>
                {node}
              </option>
            ))}
          </select>
        </div>

        {/* Tweet Count */}
        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
          <div className="text-sm text-blue-600 font-medium">Total Tweets</div>
          <div className="text-3xl font-bold text-blue-900 mt-2">
            {tweets.length}
          </div>
        </div>

        {/* Primary vs Replica */}
        <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
          <div className="text-sm text-purple-600 font-medium mb-2">Breakdown</div>
          <div className="flex justify-between text-sm mt-2">
            <div>
              <span className="text-gray-600">Primary: </span>
              <span className="font-semibold text-gray-900">
                {tweets.filter(t => !t.is_replica).length}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Replica: </span>
              <span className="font-semibold text-gray-900">
                {tweets.filter(t => t.is_replica).length}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Filter Buttons */}
      <div className="mb-4 flex gap-2">
        {['all', 'primary', 'replica'].map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === f
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {f === 'all' ? 'All' : f === 'primary' ? 'Primary' : 'Replica'}
          </button>
        ))}
      </div>

      {/* Tweets List */}
      <div className="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="p-6 text-center text-gray-500">Loading tweets...</div>
        ) : filteredTweets.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            No tweets found on this node
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-200 border-b border-gray-300">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                    Tweet ID
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                    User ID
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                    Text
                  </th>
                  <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700">
                    Type
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredTweets.map((tweet, idx) => (
                  <tr
                    key={idx}
                    className="border-b border-gray-200 hover:bg-gray-100 transition-colors"
                  >
                    <td className="px-4 py-3 text-sm font-mono text-gray-900">
                      {tweet.tweet_id}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {tweet.user_id}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">
                      <div className="max-w-xs truncate">
                        {tweet.text}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center text-sm">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          tweet.is_replica
                            ? 'bg-purple-100 text-purple-800'
                            : 'bg-green-100 text-green-800'
                        }`}
                      >
                        {tweet.is_replica ? 'Replica' : 'Primary'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Node Info Summary */}
      {selectedNode && allShards[selectedNode] && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <h3 className="font-semibold text-gray-800 mb-2">Node Information</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Node: </span>
              <span className="font-mono font-semibold text-gray-900">
                {selectedNode}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Server: </span>
              <span className="font-semibold text-gray-900">
                {allShards[selectedNode].server || 'Unknown'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
