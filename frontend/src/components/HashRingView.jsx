import React, { useEffect, useState } from 'react';
import { PolarArea } from 'react-chartjs-2';
import { Chart as ChartJS, RadialLinearScale, ArcElement, Tooltip, Legend } from 'chart.js';

ChartJS.register(RadialLinearScale, ArcElement, Tooltip, Legend);

const HashRingView = ({ ringData, logs }) => {
  const [chartData, setChartData] = useState(null);

  useEffect(() => {
    if (!ringData || !ringData.ring) return;

    // We have effectively 3 nodes, let's just show them evenly distributed
    // Consistent hashing places them on a circle, but for visualization
    // we will just show the nodes and maybe the recent tweets
    
    // Group virtual nodes by their physical Shard and mapping color appropriately
    // The nodes array now has {shard: 'Shard1', server: 'Laptop1'}
    const shardsWithServers = ringData.nodes;
    
    // Let's create a label that shows both
    const labels = shardsWithServers.map(n => `${n.shard} (${n.server})`);
    
    // Count virtual nodes per physical shard
    const dataCounts = shardsWithServers.map(n => 
      ringData.ring.filter(r => r.node === n.shard).length
    );

    // Assign consistent colors based on the SERVER, not just the shard
    const serverColors = {
      'Laptop1': 'rgba(54, 162, 235, 0.6)',   // Blue
      'Laptop2': 'rgba(255, 99, 132, 0.6)',  // Red
      'Laptop3': 'rgba(75, 192, 192, 0.6)',  // Green
      'Laptop4': 'rgba(255, 206, 86, 0.6)',  // Yellow
    };
    
    const defaultColors = [
      'rgba(153, 102, 255, 0.6)',
      'rgba(255, 159, 64, 0.6)'
    ];

    let colorIndex = 0;
    const bgColors = shardsWithServers.map(n => {
       if (serverColors[n.server]) return serverColors[n.server];
       return defaultColors[(colorIndex++) % defaultColors.length];
    });

    const data = {
      labels: labels,
      datasets: [
        {
          label: '# of Virtual Nodes',
          data: dataCounts,
          backgroundColor: bgColors,
          borderWidth: 1,
        },
      ],
    };
    
    setChartData(data);
  }, [ringData]);

  if (!chartData) return <div className="text-gray-500">Loading Hash Ring...</div>;

  return (
    <div className="bg-white p-6 rounded-xl shadow-md flex flex-col items-center">
      <h2 className="text-xl font-semibold mb-4 text-gray-800">Cluster Nodes (Consistent Hash Ring)</h2>
      <div className="w-full max-w-sm">
        <PolarArea data={chartData} options={{ responsive: true, maintainAspectRatio: true, animation: false }} />
      </div>
      <div className="mt-4 text-sm text-gray-500 text-center">
        Shows the distribution of virtual nodes across the physical storage shards on the SHA256 ring.
      </div>
    </div>
  );
};

export default HashRingView;
