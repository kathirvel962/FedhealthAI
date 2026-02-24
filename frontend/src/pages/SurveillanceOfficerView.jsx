import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  FiAlertCircle,
  FiTrendingUp,
  FiMap,
  FiActivity,
  FiShield,
  FiBarChart2,
  FiRefreshCw,
  FiBell,
} from 'react-icons/fi';
import { dashboardAPI, surveillanceAPI } from '../api';
import RealTimeAlertFeedPanel from '../components/RealTimeAlertFeedPanel';
import RiskHeatmap from '../components/RiskHeatmap';
import KPICard from '../components/KPICard';
import PremiumCard from '../components/PremiumCard';
import { LoadingSkeleton, EmptyState } from '../components/LoadingStates';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { medicalTheme, getSeverityColor } from '../components/MedicalTheme';

export default function SurveillanceOfficerView() {
  const user = JSON.parse(localStorage.getItem('user'));
  
  // State management
  const [surveillanceMetrics, setSurveillanceMetrics] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    loadAllData();
    const interval = setInterval(loadAllData, 15000); // Refresh every 15 seconds
    return () => clearInterval(interval);
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [metricsRes, alertsRes] = await Promise.all([
        dashboardAPI.getSurveillanceMetrics(),
        surveillanceAPI.getAlerts(),
      ]);
      setSurveillanceMetrics(metricsRes.data);
      setAlerts(alertsRes.data.alerts || []);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error loading surveillance data:', error);
    }
    setLoading(false);
  };

  const getSeverityColorClass = (severity) => {
    const colors = {
      'CRITICAL': 'text-red-700 bg-red-50',
      'HIGH': 'text-orange-700 bg-orange-50',
      'MEDIUM': 'text-yellow-700 bg-yellow-50',
      'LOW': 'text-green-700 bg-green-50',
    };
    return colors[severity] || 'text-gray-700 bg-gray-50 border-gray-300';
  };

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #FFFBF0 0%, #F8FAFC 50%, #FFFBF0 100%)' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-10"
        >
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-4xl sm:text-5xl font-bold gradient-text-alert mb-2">
                Surveillance Command Center
              </h1>
              <p className="text-gray-600 text-lg">Welcome {user.username} — Real-time Disease Surveillance</p>
              <p className="text-sm text-gray-500 mt-2 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full animate-pulse" style={{ background: medicalTheme.colors.danger }}></span>
                Last updated: {lastUpdated.toLocaleTimeString()}
                {autoRefresh && ' (Live)'}
              </p>
            </div>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setAutoRefresh(!autoRefresh)}
              className="btn-premium flex items-center gap-2"
              style={{
                background: autoRefresh
                  ? medicalTheme.colors.gradients.danger_gradient
                  : 'linear-gradient(135deg, #9CA3AF 0%, #6B7280 100%)',
                color: 'white'
              }}
            >
              <FiRefreshCw className={autoRefresh ? 'animate-spin' : ''} />
              {autoRefresh ? 'LIVE MODE' : 'PAUSED'}
            </motion.button>
          </div>
        </motion.div>

        {/* Summary Stats - Alert Focused */}
        {loading && !surveillanceMetrics ? (
          <LoadingSkeleton count={5} height="180px" />
        ) : surveillanceMetrics ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-5 mb-10">
            <KPICard
              title="Total Alerts"
              value={surveillanceMetrics.summary.total_alerts}
              subtitle="30-day period"
              icon={FiBell}
              gradient={medicalTheme.colors.gradients.primary_gradient}
            />

            <KPICard
              title="🔴 CRITICAL"
              value={surveillanceMetrics.summary.critical_alerts}
              subtitle="Immediate action"
              icon={FiAlertCircle}
              gradient={medicalTheme.colors.gradients.danger_gradient}
              isAlert={surveillanceMetrics.summary.critical_alerts > 0}
              isPulsing={surveillanceMetrics.summary.critical_alerts > 0}
            />

            <KPICard
              title="🟠 HIGH"
              value={surveillanceMetrics.summary.high_alerts}
              subtitle="Monitor closely"
              icon={FiActivity}
              gradient={medicalTheme.colors.gradients.alert_gradient}
              isPulsing={surveillanceMetrics.summary.high_alerts > 0}
            />

            <KPICard
              title="Avg Risk Score"
              value={surveillanceMetrics.summary.average_risk_score.toFixed(4)}
              icon={FiTrendingUp}
              gradient={medicalTheme.colors.gradients.forecast_gradient}
            />

            <KPICard
              title="Affected PHCs"
              value={surveillanceMetrics.summary.affected_phcs}
              subtitle="PHCs with alerts"
              icon={FiMap}
              gradient={medicalTheme.colors.gradients.federation_gradient}
            />
          </div>
        ) : null}

        {/* Outbreak Trend Chart */}
        {surveillanceMetrics?.outbreak_trend && surveillanceMetrics.outbreak_trend.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mb-10"
          >
            <PremiumCard
              title="📈 Outbreak Trend (30 Days)"
              subtitle="Alert severity progression"
              variant="light"
            >
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={surveillanceMetrics.outbreak_trend}>
                  <CartesianGrid strokeDasharray="3 3" stroke={medicalTheme.colors.primary + '20'} />
                  <XAxis dataKey="date" stroke={medicalTheme.colors.text.secondary} />
                  <YAxis stroke={medicalTheme.colors.text.secondary} />
                  <Tooltip
                    contentStyle={{
                      background: 'rgba(255, 255, 255, 0.95)',
                      border: `1px solid ${medicalTheme.colors.primary}40`,
                      borderRadius: '0.75rem'
                    }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="alert_count"
                    stroke={medicalTheme.colors.primary}
                    name="Total Alerts"
                    strokeWidth={3}
                  />
                  <Line
                    type="monotone"
                    dataKey="high_severity_count"
                    stroke={medicalTheme.colors.accent}
                    name="High Severity"
                    strokeWidth={3}
                  />
                  <Line
                    type="monotone"
                    dataKey="critical_severity_count"
                    stroke={medicalTheme.colors.danger}
                    name="Critical"
                    strokeWidth={3}
                  />
                </LineChart>
              </ResponsiveContainer>
            </PremiumCard>
          </motion.div>
        )}

        {/* Risk Heatmap */}
        {surveillanceMetrics && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="mb-10"
          >
            <PremiumCard
              title="🔥 Risk Distribution by City & PHC"
              subtitle="Intensity shows severity level across locations"
              variant="light"
            >
              <RiskHeatmap />
            </PremiumCard>
          </motion.div>
        )}

        {/* Alert Feed & Risk Heatmap */}
        {surveillanceMetrics && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-10">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
            >
              <RealTimeAlertFeedPanel alerts={alerts} />
            </motion.div>
          </div>
        )}

      </div>
    </div>
  );
}
