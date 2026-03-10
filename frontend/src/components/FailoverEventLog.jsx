import React, { useState, useEffect } from 'react';
import axios from 'axios';
import useWebSocket from '../hooks/useWebSocket';

const FailoverEventLog = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const { failoverEvents } = useWebSocket();

  useEffect(() => {
    fetchEvents();
    const interval = setInterval(fetchEvents, 10000); // Reduced frequency since WebSocket provides real-time updates
    return () => clearInterval(interval);
  }, []);

  // Prepend new WebSocket events to existing events
  useEffect(() => {
    if (failoverEvents.length > 0) {
      setEvents(prev => {
        const newEvents = [...failoverEvents, ...prev];
        // Remove duplicates based on timestamp
        const uniqueEvents = newEvents.filter((event, index, self) =>
          index === self.findIndex(e => e.timestamp === event.timestamp)
        );
        return uniqueEvents.slice(0, 50);
      });
    }
  }, [failoverEvents]);

  const fetchEvents = async () => {
    try {
      const res = await axios.get(`http://${window.location.hostname}:5000/failover/logs?limit=50`);
      setEvents(res.data);
      setLoading(false);
    } catch (err) {
      console.error('Failed to fetch failover logs:', err);
      setLoading(false);
    }
  };

  const getActionBadgeColor = (action) => {
    switch (action) {
      case 'read_failover':
        return 'bg-blue-500';
      case 'write_failover':
        return 'bg-purple-500';
      case 'node_down':
        return 'bg-red-500';
      case 'node_up':
        return 'bg-green-500';
      case 'read_failover_failed':
      case 'write_failover_failed':
        return 'bg-orange-500';
      default:
        return 'bg-gray-500';
    }
  };

  const formatTimestamp = (isoString) => {
    if (!isoString) return 'N/A';
    const date = new Date(isoString);
    return date.toLocaleString();
  };

  if (loading) {
    return (
      <div className="bg-white shadow-md rounded-lg p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Failover Event Log</h2>
        <p className="text-gray-500">Loading...</p>
      </div>
    );
  }

  return (
    <div className="bg-white shadow-md rounded-lg p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Failover Event Log</h2>
      
      {events.length === 0 ? (
        <p className="text-gray-500">No failover events yet</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Event Type
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tweet ID
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Primary Node
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Replica Node
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Action
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Details
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {events.map((event, index) => (
                <tr key={index} className="hover:bg-gray-50 transition">
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700">
                    {formatTimestamp(event.timestamp)}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700">
                    {event.event_type}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700">
                    {event.tweet_id || 'N/A'}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700">
                    {event.primary_node}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700">
                    {event.replica_node || 'N/A'}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className={`px-2 py-1 rounded text-xs font-semibold text-white ${getActionBadgeColor(event.action)}`}>
                      {event.action}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 max-w-xs truncate">
                    {event.details || '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default FailoverEventLog;
