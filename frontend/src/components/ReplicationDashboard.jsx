import { useEffect, useState } from 'react';
import './ReplicationDashboard.css';

export default function ReplicationDashboard() {
  const [replicationMap, setReplicationMap] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchReplicationData = async () => {
      try {
        const response = await fetch(`http://${window.location.hostname}:5000/replication/map`);
        if (!response.ok) throw new Error('Failed to fetch replication data');

        const data = await response.json();
        setReplicationMap(data.replication_map || []);
        setStats(data.stats || null);
        setError(null);
      } catch (err) {
        console.error('Error fetching replication data:', err);
        setError(err.message);
      }
    };

    setLoading(true);
    fetchReplicationData().finally(() => setLoading(false));

    const interval = setInterval(fetchReplicationData, 3000);
    return () => clearInterval(interval);
  }, []);

  const getStatusBadgeColor = (status) => {
    switch (status) {
      case 'success':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  if (loading) {
    return (
      <div className="replication-dashboard p-6">
        <div className="text-center text-gray-500">Loading replication data...</div>
      </div>
    );
  }

  return (
    <div className="replication-dashboard p-6 bg-gray-50 rounded-lg shadow-sm">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          Replication Dashboard
        </h2>
        <p className="text-gray-600">
          Monitor tweet replication across primary and replica nodes
        </p>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded text-red-700">
          {error}
        </div>
      )}

      {stats && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow-sm border-l-4 border-blue-500">
            <div className="text-sm text-gray-600">Total Tweets</div>
            <div className="text-3xl font-bold text-blue-600">
              {stats.total_tweets}
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border-l-4 border-green-500">
            <div className="text-sm text-gray-600">Successful</div>
            <div className="text-3xl font-bold text-green-600">
              {stats.successful_replications}
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border-l-4 border-red-500">
            <div className="text-sm text-gray-600">Failed</div>
            <div className="text-3xl font-bold text-red-600">
              {stats.failed_replications}
            </div>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <div className="px-6 py-4 bg-gray-100 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-800">Replication Map</h3>
        </div>

        {replicationMap.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            No tweets replicated yet
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                    Tweet ID
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                    Primary Node
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                    Primary Server
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                    Replica Node
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                    Replica Server
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                    Timestamp
                  </th>
                </tr>
              </thead>
              <tbody>
                {replicationMap.map((rep, idx) => (
                  <tr
                    key={idx}
                    className="border-b border-gray-200 hover:bg-gray-50 transition-colors"
                  >
                    <td className="px-6 py-4 text-sm font-mono text-gray-900">
                      {rep.tweet_id}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      <span className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full">
                        {rep.primary_node}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {rep.primary_server}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      <span className="px-3 py-1 bg-purple-50 text-purple-700 rounded-full">
                        {rep.replica_node || 'N/A'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {rep.replica_server}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <span
                        className={`px-3 py-1 rounded-full border text-xs font-semibold ${getStatusBadgeColor(
                          rep.status
                        )}`}
                      >
                        {rep.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {new Date(rep.timestamp).toLocaleTimeString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
