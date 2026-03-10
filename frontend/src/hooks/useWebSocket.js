import { useEffect, useState } from 'react';
import { io } from 'socket.io-client';

const defaultUrl = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:5000`;
const useWebSocket = (url = defaultUrl) => {
  const [nodeStatus, setNodeStatus] = useState({});
  const [failoverEvents, setFailoverEvents] = useState([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const socket = io(url);

    socket.on('connect', () => {
      console.log('WebSocket connected');
      setConnected(true);
    });

    socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      setConnected(false);
    });

    socket.on('node_status_update', (data) => {
      console.log('Node status update:', data);
      setNodeStatus(prev => ({
        ...prev,
        [data.shard_name]: data.status
      }));
    });

    socket.on('failover_event', (data) => {
      console.log('Failover event:', data);
      setFailoverEvents(prev => [data, ...prev].slice(0, 100));
    });

    socket.on('all_node_status', (data) => {
      console.log('All node status:', data);
      setNodeStatus(data);
    });

    return () => {
      socket.disconnect();
    };
  }, [url]);

  return { nodeStatus, failoverEvents, connected };
};

export default useWebSocket;
