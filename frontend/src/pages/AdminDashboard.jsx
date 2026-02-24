import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { adminAPI, dashboardAPI } from '../api';
import PHCReliabilityIndex from '../components/PHCReliabilityIndex';
import KPICard from '../components/KPICard';
import PremiumCard from '../components/PremiumCard';
import { LoadingSkeleton, EmptyState } from '../components/LoadingStates';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';
import { FiZap, FiTrendingUp, FiRefreshCw, FiAlertTriangle, FiCheckCircle } from 'react-icons/fi';
import { medicalTheme, getSeverityColor } from '../components/MedicalTheme';

export default function AdminDashboard() {
  const user = JSON.parse(localStorage.getItem('user'));
  const [stats, setStats] = useState(null);
  const [districtMetrics, setDistrictMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [aggregating, setAggregating] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);

  const COLORS = ['#0369A1', '#14B8A6', '#F97316', '#EF4444', '#10B981'];

  const loadDashboard = async () => {
    try {
      const districtRes = await dashboardAPI.getDistrictMetrics();
      setStats(districtRes.data);
      setDistrictMetrics(districtRes.data);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error loading dashboard:', error);
    }
  };

  const handleAggregate = async () => {
    setAggregating(true);
    try {
      await adminAPI.aggregateModels();
      alert('✓ Models aggregated successfully!');
      await loadDashboard();
    } catch (error) {
      alert('Error aggregating models: ' + (error.response?.data?.error || error.message));
      console.error('Aggregation error:', error);
    }
    setAggregating(false);
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      loadDashboard();
    }, 10000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const preparePHCData = () => {
    if (!districtMetrics?.phc_breakdown) return [];
    return districtMetrics.phc_breakdown.map(phc => ({
      phc: phc.phc_id,
      records: phc.patients,
      accuracy: (phc.local_model_accuracy * 100).toFixed(2),
      risk: phc.risk_score.toFixed(3),
    }));
  };

  const getSeverityColorClass = (severity) => {
    const colors = {
      'CRITICAL': 'text-red-700 bg-red-50',
      'HIGH': 'text-orange-700 bg-orange-50',
      'MEDIUM': 'text-yellow-700 bg-yellow-50',
      'LOW': 'text-green-700 bg-green-50',
      'UNKNOWN': 'text-gray-700 bg-gray-50'
    };
    return colors[severity] || colors['UNKNOWN'];
  };

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #FFFBF0 0%, #F8FAFC 50%, #FFFBF0 100%)' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header Section */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-10"
        >
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-4xl sm:text-5xl font-bold gradient-text-federation mb-2">
                District Strategic Dashboard
              </h1>
              <p className="text-gray-600 text-lg">Welcome {user.username} — Federated Model Oversight</p>
              <p className="text-sm text-gray-500 mt-2 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full animate-pulse" style={{ background: medicalTheme.colors.primary }}></span>
                Last updated: {lastUpdated.toLocaleTimeString()}
                {autoRefresh && ' (Auto-refresh ON)'}
              </p>
            </div>
            <div className="flex gap-3">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleAggregate}
                disabled={aggregating}
                className="btn-premium flex items-center gap-2"
                style={{
                  background: medicalTheme.colors.gradients.forecast_gradient,
                  color: 'white',
                  opacity: aggregating ? 0.7 : 1
                }}
              >
                <FiZap className={aggregating ? 'animate-spin' : ''} />
                {aggregating ? 'Aggregating...' : 'Aggregate Models'}
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setAutoRefresh(!autoRefresh)}
                className="btn-premium flex items-center gap-2"
                style={{
                  background: autoRefresh
                    ? medicalTheme.colors.gradients.success_gradient
                    : 'linear-gradient(135deg, #9CA3AF 0%, #6B7280 100%)',
                  color: 'white'
                }}
              >
                <FiRefreshCw />
                {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={loadDashboard}
                className="btn-premium flex items-center gap-2"
                style={{
                  background: medicalTheme.colors.gradients.primary_gradient,
                  color: 'white'
                }}
              >
                <FiRefreshCw />
                Refresh Now
              </motion.button>
            </div>
          </div>
        </motion.div>

        {/* KPI Cards */}
        {loading && !districtMetrics ? (
          <LoadingSkeleton count={4} height="180px" />
        ) : districtMetrics ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-10">
            <KPICard
              title="Global Model Version"
              value={districtMetrics.global_model.version || 'N/A'}
              subtitle={`Round ${districtMetrics.global_model.aggregation_round}`}
              icon={FiTrendingUp}
              gradient={medicalTheme.colors.gradients.federation_gradient}
            />

            <KPICard
              title="Global Accuracy"
              value={`${(districtMetrics.global_model.accuracy * 100).toFixed(2)}%`}
              subtitle="Federated Model"
              icon={FiCheckCircle}
              gradient={medicalTheme.colors.gradients.success_gradient}
            />

            <KPICard
              title="Contributing PHCs"
              value={`${districtMetrics?.phc_breakdown?.length || 0}/${districtMetrics?.phc_breakdown?.length || 0}`}
              subtitle="PHCs in Aggregation"
              icon={FiCheckCircle}
              gradient={medicalTheme.colors.gradients.primary_gradient}
            />

            <KPICard
              title=" Risk Score"
              value={`${((districtMetrics?.average_phc_risk_score || 0) * 100).toFixed(2)}%`}
              subtitle="Based on PHCs"
              icon={FiAlertTriangle}
              gradient={medicalTheme.colors.gradients.alert_gradient}
              isPulsing={districtMetrics?.average_phc_risk_score > 0.3}
            />
          </div>
        ) : null}

        {/* PHC Reliability Index */}
        {districtMetrics && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mb-10"
          >
            <PHCReliabilityIndex phcBreakdown={districtMetrics.phc_breakdown || []} />
          </motion.div>
        )}



        {/* High-Risk PHCs Alert */}
        {districtMetrics?.high_risk_phcs && districtMetrics.high_risk_phcs.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className="mb-10"
          >
            <PremiumCard
              title="🚨 High-Risk PHCs Requiring Attention"
              subtitle={`${districtMetrics.high_risk_phcs.length} PHCs need immediate review`}
              variant="light"
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {districtMetrics.high_risk_phcs.map(phc => (
                  <motion.div
                    key={phc.phc_id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className={`${getSeverityColorClass(phc.severity)} rounded-xl p-4 border-l-4`}
                    style={{
                      borderColor: getSeverityColor(phc.severity).bg
                    }}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-bold text-lg">{phc.phc_id}</p>
                        <p className="text-sm opacity-75">Risk: {phc.risk_score.toFixed(4)}</p>
                      </div>
                      <span className="font-bold px-3 py-1 rounded-full bg-white/50">
                        {phc.severity}
                      </span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </PremiumCard>
          </motion.div>
        )}

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-10">
          {/* PHC Accuracy Comparison */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.6 }}
          >
            <PremiumCard
              title="PHC Model Accuracy"
              subtitle="Local model performance comparison"
              variant="light"
            >
              {districtMetrics && (
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={preparePHCData()}>
                    <CartesianGrid strokeDasharray="3 3" stroke={medicalTheme.colors.primary + '20'} />
                    <XAxis dataKey="phc" stroke={medicalTheme.colors.text.secondary} />
                    <YAxis stroke={medicalTheme.colors.text.secondary} />
                    <Tooltip
                      contentStyle={{
                        background: 'rgba(255, 255, 255, 0.95)',
                        border: `1px solid ${medicalTheme.colors.primary}40`,
                        borderRadius: '0.75rem'
                      }}
                      formatter={(value) => `${value}%`}
                    />
                    <Bar dataKey="accuracy" fill={medicalTheme.colors.success} radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </PremiumCard>
          </motion.div>

          {/* PHC Risk Scores */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.6 }}
          >
            <PremiumCard
              title="PHC Risk Scores"
              subtitle="Risk severity by PHC"
              variant="light"
            >
              {districtMetrics && (
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={preparePHCData()}>
                    <CartesianGrid strokeDasharray="3 3" stroke={medicalTheme.colors.primary + '20'} />
                    <XAxis dataKey="phc" stroke={medicalTheme.colors.text.secondary} />
                    <YAxis stroke={medicalTheme.colors.text.secondary} />
                    <Tooltip
                      contentStyle={{
                        background: 'rgba(255, 255, 255, 0.95)',
                        border: `1px solid ${medicalTheme.colors.primary}40`,
                        borderRadius: '0.75rem'
                      }}
                    />
                    <Bar dataKey="risk" fill={medicalTheme.colors.accent} radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </PremiumCard>
          </motion.div>
        </div>

        {/* PHC Breakdown Table */}
        {districtMetrics?.phc_breakdown && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.7 }}
          >
            <PremiumCard
              title="PHC Performance Breakdown"
              subtitle={`${districtMetrics.phc_breakdown.length} participating PHCs`}
              variant="light"
            >
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gradient-to-r from-yellow-50 to-amber-50 border-b-2 font-bold" style={{ borderColor: medicalTheme.colors.primary + '60' }}>
                    <tr>
                      <th className="px-4 py-3 text-left font-semibold text-gray-900">PHC</th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-900">Local Model</th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-900">Accuracy</th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-900">Risk Score</th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-900">Severity</th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-900">Patients</th>
                    </tr>
                  </thead>
                  <tbody>
                    {districtMetrics.phc_breakdown.map((phc, idx) => (
                      <motion.tr
                        key={phc.phc_id}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: idx * 0.05 }}
                        className="border-b hover:bg-yellow-50/50 transition-colors"
                        style={{ borderColor: medicalTheme.colors.primary + '10' }}
                      >
                        <td className="px-4 py-3 font-semibold text-gray-900">{phc.phc_id}</td>
                        <td className="px-4 py-3 text-gray-700">{phc.local_model_version}</td>
                        <td className="px-4 py-3 text-gray-700">{(phc.local_model_accuracy * 100).toFixed(2)}%</td>
                        <td className="px-4 py-3 text-gray-700">{phc.risk_score.toFixed(4)}</td>
                        <td className={`px-4 py-3 font-semibold rounded-lg ${getSeverityColorClass(phc.severity)}`}>
                          {phc.severity}
                        </td>
                        <td className="px-4 py-3 text-gray-700">{phc.patients}</td>
                      </motion.tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </PremiumCard>
          </motion.div>
        )}
      </div>
    </div>
  );
}
