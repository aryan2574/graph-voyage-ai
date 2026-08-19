import { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Activity, TrendingUp, CheckCircle, Clock, AlertTriangle, RefreshCw } from 'lucide-react';
import { travelApi } from '../services/api';
import type { MetricsResponse } from '../types';
import './Dashboard.css';

const Dashboard = () => {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchMetrics = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await travelApi.getMetrics();
      setMetrics(data);
      setLastUpdated(new Date());
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || 'Failed to fetch metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchMetrics, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b'];

  if (loading && !metrics) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading metrics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-error card">
        <AlertTriangle className="error-icon" />
        <div>
          <h3>Error Loading Metrics</h3>
          <p>{error}</p>
          <button onClick={fetchMetrics} className="btn btn-primary">
            <RefreshCw size={18} />
            Retry
          </button>
        </div>
      </div>
    );
  }

  const rollingMetrics = metrics?.rolling_metrics;
  const timeMetrics = metrics?.last_24_hours;

  // Prepare data for charts with proper null checks
  const hourlyData = timeMetrics?.labels && timeMetrics?.hourly_counts && timeMetrics?.hourly_pass_rates
    ? timeMetrics.labels.map((label, index) => ({
        time: label,
        requests: timeMetrics.hourly_counts[index] || 0,
        passRate: ((timeMetrics.hourly_pass_rates[index] || 0) * 100).toFixed(1),
      }))
    : [];

  const statusData = rollingMetrics && rollingMetrics.evaluated_count > 0 ? [
    { name: 'Passed', value: Math.round(rollingMetrics.pass_rate * rollingMetrics.evaluated_count / 100) },
    { name: 'Failed', value: Math.round((100 - rollingMetrics.pass_rate) * rollingMetrics.evaluated_count / 100) },
  ] : [
    { name: 'No Data', value: 1 }
  ];

  return (
    <div className="dashboard fade-in">
      <div className="dashboard-header">
        <div>
          <h1>System Metrics Dashboard</h1>
          <p className="dashboard-subtitle">
            Real-time monitoring of AI travel planning performance
          </p>
        </div>
        <button 
          onClick={fetchMetrics} 
          className="btn btn-secondary refresh-btn"
          disabled={loading}
        >
          <RefreshCw size={18} className={loading ? 'loading-spinner' : ''} />
          Refresh
        </button>
      </div>

      {metrics?.note && (
        <div className="info-banner">
          <Activity size={18} />
          <p>{metrics.note}</p>
        </div>
      )}

      <div className="metrics-grid">
        <div className="metric-card card">
          <div className="metric-icon gradient-bg">
            <Activity />
          </div>
          <div className="metric-content">
            <p className="metric-label">Total Requests</p>
            <p className="metric-value">{rollingMetrics?.total_requests?.toLocaleString() || '0'}</p>
            <p className="metric-detail">
              {rollingMetrics?.evaluated_count || 0} evaluated (10% sample)
            </p>
          </div>
        </div>

        <div className="metric-card card">
          <div className="metric-icon success-bg">
            <CheckCircle />
          </div>
          <div className="metric-content">
            <p className="metric-label">Pass Rate</p>
            <p className="metric-value">{rollingMetrics?.pass_rate?.toFixed(1) || '0.0'}%</p>
            <p className="metric-detail">
              All checks passed
            </p>
          </div>
        </div>

        <div className="metric-card card">
          <div className="metric-icon warning-bg">
            <TrendingUp />
          </div>
          <div className="metric-content">
            <p className="metric-label">Safety Rate</p>
            <p className="metric-value">{rollingMetrics?.safety_rate?.toFixed(1) || '0.0'}%</p>
            <p className="metric-detail">
              Safety checks passed
            </p>
          </div>
        </div>

        <div className="metric-card card">
          <div className="metric-icon info-bg">
            <Clock />
          </div>
          <div className="metric-content">
            <p className="metric-label">Avg Latency</p>
            <p className="metric-value">{rollingMetrics?.avg_latency?.toFixed(2) || '0.00'}s</p>
            <p className="metric-detail">
              P95: {rollingMetrics?.p95_latency?.toFixed(2) || '0.00'}s
            </p>
          </div>
        </div>
      </div>

      <div className="charts-grid">
        <div className="chart-card card">
          <div className="chart-header">
            <h3>Requests Over Time (24 Hours)</h3>
            <p className="chart-subtitle">Hourly request volume</p>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={hourlyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis 
                dataKey="time" 
                stroke="#94a3b8"
                style={{ fontSize: '0.75rem' }}
              />
              <YAxis 
                stroke="#94a3b8"
                style={{ fontSize: '0.75rem' }}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #e2e8f0',
                  borderRadius: '0.5rem',
                }}
              />
              <Legend />
              <Bar dataKey="requests" fill="#6366f1" name="Requests" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card card">
          <div className="chart-header">
            <h3>Pass Rate Trend</h3>
            <p className="chart-subtitle">Success rate over time</p>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={hourlyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis 
                dataKey="time" 
                stroke="#94a3b8"
                style={{ fontSize: '0.75rem' }}
              />
              <YAxis 
                stroke="#94a3b8"
                style={{ fontSize: '0.75rem' }}
                domain={[0, 100]}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #e2e8f0',
                  borderRadius: '0.5rem',
                }}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="passRate" 
                stroke="#10b981" 
                strokeWidth={2}
                name="Pass Rate (%)"
                dot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card card">
          <div className="chart-header">
            <h3>Request Status Distribution</h3>
            <p className="chart-subtitle">Passed vs failed requests</p>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={statusData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {statusData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="update-info">
        <Clock size={14} />
        <span>Last updated: {lastUpdated.toLocaleTimeString()}</span>
      </div>
    </div>
  );
};

export default Dashboard;
