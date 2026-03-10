import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Bar, Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const ClusterHealthGraph = () => {
  const [nodeStatus, setNodeStatus] = useState({});
  const [failoverEvents, setFailoverEvents] = useState([]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [statusRes, eventsRes] = await Promise.all([
        axios.get(`http://${window.location.hostname}:5000/nodes/status`),
        axios.get(`http://${window.location.hostname}:5000/failover/logs?limit=100`)
      ]);
      setNodeStatus(statusRes.data);
      setFailoverEvents(eventsRes.data);
    } catch (err) {
      console.error('Failed to fetch cluster health data:', err);
    }
  };

  const getBarChartData = () => {
    const statusCounts = { ACTIVE: 0, DOWN: 0, RECOVERING: 0 };
    Object.values(nodeStatus).forEach(status => {
      if (statusCounts.hasOwnProperty(status)) {
        statusCounts[status]++;
      }
    });

    return {
      labels: ['ACTIVE', 'DOWN', 'RECOVERING'],
      datasets: [
        {
          label: 'Node Count',
          data: [statusCounts.ACTIVE, statusCounts.DOWN, statusCounts.RECOVERING],
          backgroundColor: ['#10b981', '#ef4444', '#f59e0b'],
          borderColor: ['#059669', '#dc2626', '#d97706'],
          borderWidth: 1
        }
      ]
    };
  };

  const getLineChartData = () => {
    // Group events by hour for the last 24 hours
    const now = new Date();
    const hourlyData = {};
    
    for (let i = 23; i >= 0; i--) {
      const hour = new Date(now.getTime() - i * 60 * 60 * 1000);
      const hourKey = hour.getHours();
      hourlyData[hourKey] = 0;
    }

    failoverEvents.forEach(event => {
      const eventDate = new Date(event.timestamp);
      const hourKey = eventDate.getHours();
      if (hourlyData.hasOwnProperty(hourKey)) {
        hourlyData[hourKey]++;
      }
    });

    const labels = Object.keys(hourlyData).map(h => `${h}:00`);
    const data = Object.values(hourlyData);

    return {
      labels,
      datasets: [
        {
          label: 'Failover Events',
          data,
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.4
        }
      ]
    };
  };

  const barOptions = {
    animation: false,
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      title: {
        display: true,
        text: 'Node Status Distribution'
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 1
        }
      }
    }
  };

  const lineOptions = {
    animation: false,
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      title: {
        display: true,
        text: 'Failover Events (Last 24 Hours)'
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 1
        }
      }
    }
  };

  return (
    <div className="bg-white shadow-md rounded-lg p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Cluster Health Metrics</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-50 rounded-lg p-4" style={{ height: '300px' }}>
          <Bar data={getBarChartData()} options={barOptions} />
        </div>
        
        <div className="bg-gray-50 rounded-lg p-4" style={{ height: '300px' }}>
          <Line data={getLineChartData()} options={lineOptions} />
        </div>
      </div>
    </div>
  );
};

export default ClusterHealthGraph;
