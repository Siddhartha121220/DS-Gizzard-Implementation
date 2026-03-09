import React, { useState, useEffect } from 'react';
import axios from 'axios';
import useWebSocket from '../hooks/useWebSocket';

const NodeStatusDashboard = () => {
  const [healthInfo, setHealthInfo] = useState({});
  const [loading, setLoading] = useState(true);
  const { nodeStatus, connected } = useWebSocket();

  useEffect(() => {
    fetchHealthInfo();
    const interval = setInterval(fetchHealthInfo, 10000); // Reduced frequency since WebSocket provides real-time updates
    return () => clearInterval(interval);
  }, []);

  // Update health info when WebSocket status changes
  useEffect(() => {
    if (Object.keys(nodeStatus).length > 0) {
      fetchHealthInfo();
    }
  }, [nodeStatus]);

  const fetchHealthInfo = async () => {
    try {
      const res = await axios.get('http://localhost:5000/nodes/health');
      setHealthInfo(res.data);
      setLoading(false);
    } catch (err) {
      console.error('Failed to fetch health info:', err);
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'ACTIVE':
        return 'bg-green-500';
      case 'DOWN':
        return 'bg-red-500';
      case 'RECOVERING':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-500';
    }
  };

  const formatTimestamp = (isoString) => {
    if (!isoString) return 'N/A';
    const date = new Date(isoString);
    return date.toLocaleTimeString();
  };

  if (loading) {
    return (
      <div className="bg-white shadow-md rounded-lg p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Node Health Status</h2>
        <p className="text-gray-500">Loading...</p>
      </div>
    );
  }

  return (
    <div className="bg-white shadow-md rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-gray-800">Node Health Status</h2>
        <div className="flex items-center">
          <div className={`w-3 h-3 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'} mr-2`}></div>
          <span className="text-sm text-gray-600">{connected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>
      
      {Object.keys(healthInfo).length === 0 ? (
        <p className="text-gray-500">No nodes available</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(healthInfo).map(([shardName, info]) => (
            <div key={shardName} className="border border-gray-200 rounded-lg p-4 hover:shadow-lg transition">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-lg font-semibold text-gray-700">{shardName}</h3>
                <span className={`px-3 py-1 rounded-full text-white text-sm font-semibold ${getStatusColor(info.status)}`}>
                  {info.status}
                </span>
              </div>
              
              <div className="text-sm text-gray-600 space-y-1">
                <p>
                  <span className="font-medium">Last Heartbeat:</span>{' '}
                  {formatTimestamp(info.last_heartbeat)}
                </p>
                
                {info.status === 'RECOVERING' && (
                  <p>
                    <span className="font-medium">Recovery Progress:</span>{' '}
                    {info.consecutive_successes}/3
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default NodeStatusDashboard;
