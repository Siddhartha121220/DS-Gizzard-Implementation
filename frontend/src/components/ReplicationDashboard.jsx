import { useEffect, useState } from 'react';
import './ReplicationDashboard.css';

export default function ReplicationDashboard() {
  const [replicationMap, setReplicationMap] = useState([]);
  const [topology, setTopology] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [mapRes, topRes] = await Promise.all([
          fetch(`http://${window.location.hostname === 'localhost' ? '127.0.0.1' : window.location.hostname}:5000/replication/map`),
          fetch(`http://${window.location.hostname === 'localhost' ? '127.0.0.1' : window.location.hostname}:5000/replication/topology`)
        ]);

        if (!mapRes.ok || !topRes.ok) throw new Error('Failed to fetch replication data');

        const mapData = await mapRes.json();
        const topData = await topRes.json();

        setReplicationMap(mapData.replication_map || []);
        setStats(mapData.stats || null);
        setTopology(topData || []);
        setError(null);
      } catch (err) {
        console.error('Error fetching replication data:', err);
        setError(err.message);
      }
    };

    setLoading(true);
    fetchData().finally(() => setLoading(false));

    const interval = setInterval(fetchData, 3000);
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
      <div className="replication-dashboard p-6 text-center text-gray-500">
        Loading replication data...
      </div>
    );
  }

  return (
    <div className="replication-dashboard p-6 bg-gray-50 rounded-lg shadow-sm space-y-8">
      <div className="flex justify-between items-end border-b border-gray-200 pb-4">
        <div>
          <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight">
            Replication Dashboard
          </h2>
          <p className="text-gray-500 mt-1">
            Real-time status of data redundancy and host-aware topology.
          </p>
        </div>
        {stats && (
          <div className="flex gap-4">
            <div className="text-right">
              <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Total</div>
              <div className="text-xl font-bold text-gray-900">{stats.total_tweets}</div>
            </div>
            <div className="text-right">
              <div className="text-xs font-semibold text-green-500 uppercase tracking-wider">Synced</div>
              <div className="text-xl font-bold text-green-600">{stats.successful_replications}</div>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 flex items-center gap-3">
          <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
          {error}
        </div>
      )}

      {/* REPLICATION TOPOLOGY (Static Strategy) */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-100 flex items-center justify-between">
          <h3 className="text-lg font-bold text-gray-800">Cluster Replication Strategy</h3>
          <span className="text-xs font-medium px-2 py-1 bg-blue-100 text-blue-700 rounded uppercase">Host-Aware</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-gray-50/50">
                <th className="px-6 py-3 text-xs font-bold text-gray-500 uppercase tracking-wider">Primary Shard</th>
                <th className="px-6 py-3 text-xs font-bold text-gray-500 uppercase tracking-wider">Primary Host</th>
                <th className="px-6 py-3 text-center text-gray-400">➜</th>
                <th className="px-6 py-3 text-xs font-bold text-gray-500 uppercase tracking-wider">Replica Shard</th>
                <th className="px-6 py-3 text-xs font-bold text-gray-500 uppercase tracking-wider">Replica Host</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {topology.map((top, idx) => (
                <tr key={idx} className="hover:bg-blue-50/30 transition-colors">
                  <td className="px-6 py-4">
                    <span className="font-bold text-blue-600">{top.primary_node}</span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    <div className="font-medium text-gray-900">{top.primary_server}</div>
                    <div className="text-xs text-gray-400 font-mono">{top.primary_host}</div>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-gray-300 text-lg">→</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="font-bold text-purple-600">{top.replica_node}</span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    <div className="font-medium text-gray-900">{top.replica_server}</div>
                    <div className="text-xs text-gray-400 font-mono">{top.replica_host}</div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* REPLICATION LOG (Live Tweets) */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-100">
          <h3 className="text-lg font-bold text-gray-800">Recent Replication Events</h3>
        </div>
        {replicationMap.length === 0 ? (
          <div className="p-12 text-center">
            <div className="text-4xl mb-4">📜</div>
            <p className="text-gray-400 font-medium whitespace-pre-wrap">No tweets have been replicated yet.
              Store a tweet to see live replication routing.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-gray-50/50">
                  <th className="px-6 py-3 text-xs font-bold text-gray-500 uppercase tracking-wider">Tweet ID</th>
                  <th className="px-6 py-3 text-xs font-bold text-gray-500 uppercase tracking-wider">Primary Node</th>
                  <th className="px-6 py-3 text-xs font-bold text-gray-500 uppercase tracking-wider">Replica Node</th>
                  <th className="px-6 py-3 text-xs font-bold text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-xs font-bold text-gray-500 uppercase tracking-wider">Completed</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {replicationMap.map((rep, idx) => (
                  <tr key={idx} className="hover:bg-gray-50/50 transition-colors">
                    <td className="px-6 py-4 text-sm font-mono text-gray-500">
                      {rep.tweet_id.substring(0, 8)}...
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm font-semibold text-gray-900">{rep.primary_node}</div>
                      <div className="text-xs text-gray-400">{rep.primary_server}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm font-semibold text-gray-900">{rep.replica_node || 'N/A'}</div>
                      <div className="text-xs text-gray-400">{rep.replica_server}</div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase border ${getStatusBadgeColor(rep.status)}`}>
                        {rep.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-xs text-gray-400">
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
