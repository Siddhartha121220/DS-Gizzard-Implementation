import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ServerView = ({ serversData }) => {
  const [shardContents, setShardContents] = useState({});
  const [serverStatus, setServerStatus] = useState({});
  const [loading, setLoading] = useState(false);
  const [editingServer, setEditingServer] = useState(null);
  const [newServerName, setNewServerName] = useState("");

  const handleRenameSubmit = async (oldName) => {
    if (!newServerName || newServerName === oldName) {
      setEditingServer(null);
      return;
    }
    try {
      await axios.post(`http://localhost:5000/servers/${oldName}/rename`, { new_name: newServerName });
      setEditingServer(null);
      window.location.reload(); 
    } catch (err) {
      console.error("Failed to rename server:", err);
      // Wait for 1s then reset
      setTimeout(() => { setEditingServer(null) }, 1000)
    }
  };

  const startEdit = (serverName) => {
    setEditingServer(serverName);
    setNewServerName(serverName);
  };


  const fetchData = async () => {
    setLoading(true);
    try {
      const [shardsRes, statusRes] = await Promise.all([
        axios.get('http://localhost:5000/shards').catch(e => ({ data: {} })),
        axios.get('http://localhost:5000/servers/status').catch(e => ({ data: {} }))
      ]);
      setShardContents(shardsRes.data);
      setServerStatus(statusRes.data);
    } catch (err) {
      console.error("Failed to fetch data:", err);
    } finally {
      setLoading(false);
    }
  };

  const startServer = async (serverName) => {
    try {
      await axios.post(`http://localhost:5000/servers/${serverName}/start`);
      fetchData();
    } catch (err) {
      console.error("Failed to start server:", err);
    }
  };

  const stopServer = async (serverName) => {
    try {
      await axios.post(`http://localhost:5000/servers/${serverName}/stop`);
      fetchData();
    } catch (err) {
      console.error("Failed to stop server:", err);
    }
  };

  useEffect(() => {
    fetchData();
  }, [serversData]); 

  // Add an interval to refresh the shard contents periodically
  useEffect(() => {
    const interval = setInterval(() => {
      fetchData();
    }, 5000);
    return () => clearInterval(interval);
  }, []);


  if (!serversData) return <div className="text-gray-500 flex items-center justify-center p-10"><span className="animate-pulse">Loading Servers Infrastructure...</span></div>;

  return (
    <div className="bg-white p-6 rounded-xl shadow-md flex flex-col h-full border-t-4 border-indigo-500">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold text-gray-800 tracking-tight">Physical Servers</h2>
        <button 
          onClick={fetchData}
          className={`text-sm bg-indigo-50 hover:bg-indigo-100 text-indigo-700 px-3 py-1.5 rounded-md transition-colors flex items-center ${loading ? 'opacity-50' : ''}`}
          disabled={loading}
        >
          <svg className={`w-4 h-4 mr-1 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
          Refresh Data
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 overflow-hidden">
        {Object.entries(serversData).map(([serverName, serverInfo]) => (
          <div key={serverName} className="border border-gray-200 rounded-xl bg-gray-50 flex flex-col overflow-hidden shadow-sm hover:shadow transition-shadow">
            
            <div className="bg-white border-b border-gray-200 p-4 flex justify-between items-center">
              <div className="flex items-center">
                <svg className="w-5 h-5 mr-2 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" /></svg>
                {editingServer === serverName ? (
                  <div className="flex items-center">
                    <input 
                      type="text" 
                      value={newServerName} 
                      onChange={(e) => setNewServerName(e.target.value)} 
                      className="border border-indigo-300 rounded px-2 py-1 text-sm font-bold text-indigo-900 w-32 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      autoFocus
                      onKeyDown={(e) => e.key === 'Enter' && handleRenameSubmit(serverName)}
                    />
                    <button onClick={() => handleRenameSubmit(serverName)} className="ml-2 text-xs bg-indigo-500 text-white px-2 py-1 rounded hover:bg-indigo-600 flex-shrink-0">Save</button>
                    <button onClick={() => setEditingServer(null)} className="ml-1 text-xs text-gray-500 hover:text-gray-700 flex-shrink-0">Cancel</button>
                  </div>
                ) : (
                  <h3 className="text-lg font-bold text-indigo-900 flex items-center group cursor-pointer" onClick={() => startEdit(serverName)} title="Click to rename server">
                    {serverName}
                    <svg className="w-3.5 h-3.5 ml-1.5 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                    </svg>
                  </h3>
                )}
                {editingServer !== serverName && (
                  <span className={`ml-3 w-2.5 h-2.5 rounded-full flex-shrink-0 ${serverStatus[serverName] === 'up' ? 'bg-green-500' : 'bg-red-500'}`}></span>
                )}
              </div>
              <div className="ml-2">
                {serverStatus[serverName] === 'up' ? (
                  <button onClick={() => stopServer(serverName)} className="text-xs bg-red-50 text-red-600 hover:bg-red-100 px-2.5 py-1 rounded shadow-sm border border-red-200 transition-colors">
                    Stop Server
                  </button>
                ) : (
                  <button onClick={() => startServer(serverName)} className="text-xs bg-green-50 text-green-700 hover:bg-green-100 px-2.5 py-1 rounded shadow-sm border border-green-200 transition-colors">
                    Start Server
                  </button>
                )}
              </div>
            </div>

            <div className="p-4 flex-1 flex flex-col gap-4">
              {Object.entries(serverInfo.shards).map(([shardName, shardConfig]) => {
                const content = shardContents[shardName]?.tweets || [];
                const hasError = shardContents[shardName]?.error;
                
                return (
                  <div key={shardName} className="bg-white rounded-lg border border-gray-200 overflow-hidden flex flex-col">
                    <div className="bg-gray-100 p-2 border-b border-gray-200 flex justify-between items-center">
                      <span className="font-bold text-gray-700 text-sm flex items-center">
                        <div className={`w-2 h-2 rounded-full mr-2 ${hasError ? 'bg-red-500' : 'bg-green-500'}`}></div>
                        {shardName}
                      </span>
                      <span className="text-[10px] text-gray-500 font-mono bg-white px-1.5 py-0.5 rounded border border-gray-200">
                        {shardConfig.host}:{shardConfig.port}
                      </span>
                    </div>
                    
                    <div className="p-3 bg-gray-50 min-h-[80px] max-h-[120px] overflow-y-auto">
                      {hasError ? (
                        <div className="text-xs text-red-500 italic flex items-center justify-center h-full">Node Offline ({hasError})</div>
                      ) : content.length === 0 ? (
                        <div className="text-xs text-gray-400 italic flex items-center justify-center h-full">No data stored on this shard</div>
                      ) : (
                        <ul className="space-y-2">
                          {content.map((tweet, i) => (
                            <li key={i} className="text-xs bg-white p-2 rounded shadow-sm border-l-2 border-indigo-400 flex flex-col">
                              <span className="font-semibold text-gray-800 mb-1">ID: {tweet.tweet_id} <span className="text-gray-400 font-normal">by {tweet.user_id}</span></span>
                              <span className="text-gray-600 truncate" title={tweet.text}>{tweet.text}</span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ServerView;
