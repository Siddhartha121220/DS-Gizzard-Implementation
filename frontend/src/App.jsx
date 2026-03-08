import React, { useState, useEffect } from 'react';
import axios from 'axios';
import HashRingView from './components/HashRingView';
import RouterLogs from './components/RouterLogs';
import TweetForm from './components/TweetForm';
import ServerView from './components/ServerView';

function App() {
  const [ringData, setRingData] = useState(null);
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    fetchRingData();
    // In a real app we might poll this or use websockets
    // for this demo, we fetch it once on load
  }, []);

  const fetchRingData = async () => {
    try {
      const res = await axios.get('http://localhost:5000/hash-ring');
      setRingData(res.data);
    } catch (err) {
      console.error("Failed to fetch hash ring data:", err);
    }
  };

  const handleNewTweetRoute = (logEntry) => {
    setLogs(prev => [logEntry, ...prev]);
    // Optionally refresh ring data if node status changed
  };

  return (
    <div className="min-h-screen bg-gray-100 text-gray-900 font-sans p-6 md:p-10">
      <div className="max-w-6xl mx-auto space-y-8">
        
        <header className="mb-10 text-center md:text-left">
          <h1 className="text-4xl font-extrabold text-blue-900 tracking-tight">Gizzard Router Dashboard</h1>
          <p className="text-gray-500 mt-2 text-lg">Consistent Hashing & Shard Distribution Visualization</p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          <div className="lg:col-span-1 flex flex-col gap-8">
            <TweetForm onTweetRouted={handleNewTweetRoute} />
          </div>

          <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-8">
            <HashRingView ringData={ringData} logs={logs} />
            <RouterLogs logs={logs} />
          </div>

        </div>

        <div className="w-full">
          <ServerView serversData={ringData?.servers} />
        </div>
      </div>
    </div>
  );
}

export default App;
