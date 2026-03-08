import React from 'react';

const RouterLogs = ({ logs }) => {
  return (
    <div className="bg-white p-6 rounded-xl shadow-md h-full flex flex-col">
      <h2 className="text-xl font-semibold mb-4 text-gray-800">Router Logs</h2>
      <div className="flex-1 overflow-y-auto bg-gray-50 p-4 rounded-lg border border-gray-100 min-h-[200px] max-h-[400px]">
        {logs.length === 0 ? (
          <p className="text-gray-400 italic text-center mt-10">No routing events yet</p>
        ) : (
          <ul className="space-y-3">
            {logs.map((log, index) => (
              <li key={index} className="text-sm font-mono bg-white p-3 rounded shadow-sm border-l-4 border-blue-500 flex justify-between items-center">
                <span className="flex items-center">
                  <span className="text-blue-600 font-bold">ID {log.tweet_id}</span> 
                  <span className="text-gray-400 mx-2">→</span> 
                  <span className="flex flex-col">
                    <span className="text-green-600 font-bold">{log.node}</span>
                    <span className="text-[10px] text-gray-500 bg-gray-100 px-1 rounded inline-block mt-0.5 w-fit">{log.server}</span>
                  </span>
                </span>
                <span className="text-xs text-gray-400 truncate w-24 ml-4 text-right" title={log.hash_value}>
                  Hash: {log.hash_value.substring(0, 8)}...
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default RouterLogs;
