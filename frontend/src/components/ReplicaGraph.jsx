import { useEffect, useState } from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';
import './ReplicaGraph.css';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title);

export default function ReplicaGraph() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [chartType, setChartType] = useState('pie');

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch(`http://${window.location.hostname}:5000/replication/map`);
        if (!response.ok) throw new Error('Failed to fetch replication stats');

        const data = await response.json();
        setStats(data.stats || null);
        setError(null);
      } catch (err) {
        console.error('Error fetching stats:', err);
        setError(err.message);
      }
    };

    setLoading(true);
    fetchStats().finally(() => setLoading(false));
    const interval = setInterval(fetchStats, 3000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="replica-graph p-6">
        <div className="text-center text-gray-500">Loading chart data...</div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="replica-graph p-6">
        <div className="text-center text-red-500">{error || 'No data available'}</div>
      </div>
    );
  }

  // Prepare data for pie chart (tweets per node)
  const nodeLabels = Object.keys(stats.by_node || {});
  const primaryCounts = nodeLabels.map(node => stats.by_node[node].primary || 0);
  const replicaCounts = nodeLabels.map(node => stats.by_node[node].replica || 0);
  const totalCounts = nodeLabels.map(node =>
    (stats.by_node[node].primary || 0) + (stats.by_node[node].replica || 0)
  );

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

  const pieChartData = {
    labels: nodeLabels,
    datasets: [
      {
        label: 'Total Tweets Stored',
        data: totalCounts,
        backgroundColor: COLORS.slice(0, nodeLabels.length),
        borderColor: '#fff',
        borderWidth: 2,
      },
    ],
  };

  const barChartData = {
    labels: nodeLabels,
    datasets: [
      {
        label: 'Primary Tweets',
        data: primaryCounts,
        backgroundColor: '#3B82F6',
        borderColor: '#1E40AF',
        borderWidth: 1,
      },
      {
        label: 'Replica Tweets',
        data: replicaCounts,
        backgroundColor: '#10B981',
        borderColor: '#065F46',
        borderWidth: 1,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          padding: 15,
          font: {
            size: 12,
            weight: 500,
          },
        },
      },
    },
  };

  return (
    <div className="replica-graph bg-white rounded-lg shadow-sm p-6">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Node Storage Distribution</h2>
          <p className="text-gray-600 text-sm mt-1">
            Visualize how tweets are distributed across nodes
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setChartType('pie')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${chartType === 'pie'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
          >
            Pie Chart
          </button>
          <button
            onClick={() => setChartType('bar')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${chartType === 'bar'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
          >
            Bar Chart
          </button>
        </div>
      </div>

      <div className="chart-container" style={{ position: 'relative', height: '400px' }}>
        {chartType === 'pie' ? (
          <Pie data={pieChartData} options={chartOptions} />
        ) : (
          <Bar data={barChartData} options={chartOptions} />
        )}
      </div>

      {stats && (
        <div className="grid grid-cols-3 gap-4 mt-8">
          <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div className="text-sm text-blue-600 font-medium">Total Tweets</div>
            <div className="text-3xl font-bold text-blue-900 mt-2">
              {stats.total_tweets}
            </div>
          </div>
          <div className="p-4 bg-green-50 rounded-lg border border-green-200">
            <div className="text-sm text-green-600 font-medium">Successful Replications</div>
            <div className="text-3xl font-bold text-green-900 mt-2">
              {stats.successful_replications}
            </div>
          </div>
          <div className="p-4 bg-red-50 rounded-lg border border-red-200">
            <div className="text-sm text-red-600 font-medium">Failed Replications</div>
            <div className="text-3xl font-bold text-red-900 mt-2">
              {stats.failed_replications}
            </div>
          </div>
        </div>
      )}

      <div className="mt-8 bg-gray-50 rounded-lg p-4">
        <h3 className="font-semibold text-gray-800 mb-4">Storage Breakdown by Node</h3>
        <div className="space-y-2">
          {nodeLabels.map((node, idx) => (
            <div key={node} className="flex items-center justify-between p-2 bg-white rounded border border-gray-200">
              <div className="flex items-center gap-3">
                <div
                  className="w-4 h-4 rounded"
                  style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                ></div>
                <span className="font-medium text-gray-700">{node}</span>
              </div>
              <div className="flex gap-6 text-sm">
                <div>
                  <span className="text-gray-600">Primary: </span>
                  <span className="font-semibold text-gray-900">
                    {stats.by_node[node].primary || 0}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Replica: </span>
                  <span className="font-semibold text-gray-900">
                    {stats.by_node[node].replica || 0}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Total: </span>
                  <span className="font-semibold text-gray-900">
                    {(stats.by_node[node].primary || 0) + (stats.by_node[node].replica || 0)}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
