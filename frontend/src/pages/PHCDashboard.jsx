import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { dashboardAPI, phcAPI } from '../api';
import PatientForm from '../components/PatientForm';
import TriageConfidenceRadar from '../components/TriageConfidenceRadar';
import AnomalyRadarPulse from '../components/AnomalyRadarPulse';
import SymptomDistributionVisualization from '../components/SymptomDistributionVisualization';
import KPICard from '../components/KPICard';
import PremiumCard from '../components/PremiumCard';
import { LoadingSkeleton, EmptyState } from '../components/LoadingStates';
import { FiUsers, FiActivity, FiAlertTriangle, FiTrendingDown, FiCheckCircle, FiRefreshCw } from 'react-icons/fi';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { medicalTheme, getDriftStatus } from '../components/MedicalTheme';

export default function PHCDashboard() {
  const user = JSON.parse(localStorage.getItem('user'));
  const phcId = user.phc_id || `PHC${user.id.slice(-1)}`;
  
  const [patients, setPatients] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [showPatientForm, setShowPatientForm] = useState(false);

  useEffect(() => {
    loadDashboard();
    const interval = setInterval(loadDashboard, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const [patientsRes, metricsRes] = await Promise.all([
        phcAPI.getPatients(),
        dashboardAPI.getPHCMetrics()
      ]);
      setPatients(patientsRes.data.patients || []);
      setMetrics(metricsRes.data);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error loading dashboard:', error);
    }
    setLoading(false);
  };

  const handlePatientSubmitted = () => {
    loadDashboard();
    setShowPatientForm(false);
  };

  const getSeverityColor = (severity) => {
    const colors = {
      'CRITICAL': 'text-red-700 bg-red-50',
      'HIGH': 'text-orange-700 bg-orange-50',
      'MEDIUM': 'text-yellow-700 bg-yellow-50',
      'LOW': 'text-green-700 bg-green-50',
      'UNKNOWN': 'text-gray-700 bg-gray-50'
    };
    return colors[severity] || colors['UNKNOWN'];
  };

  const driftStatus = metrics?.drift ? getDriftStatus(metrics.drift.accuracy_drop_percentage) : null;

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
              <h1 className="text-4xl sm:text-5xl font-bold gradient-text-primary mb-2">
                Clinical Dashboard
              </h1>
              <p className="text-gray-600 text-lg">{phcId} — Welcome {user.username}</p>
              <p className="text-sm text-gray-500 mt-2 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full animate-pulse" style={{ background: medicalTheme.colors.success }}></span>
                Last updated: {lastUpdated.toLocaleTimeString()}
              </p>
            </div>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={loadDashboard}
              disabled={loading}
              className="btn-premium flex items-center gap-2"
              style={{
                background: medicalTheme.colors.gradients.primary_gradient,
                color: 'white',
                opacity: loading ? 0.7 : 1
              }}
            >
              <FiRefreshCw className={loading ? 'animate-spin' : ''} />
              {loading ? 'Refreshing...' : 'Refresh'}
            </motion.button>
          </div>
        </motion.div>

        {/* KPI Metrics Grid */}
        {loading && !metrics ? (
          <LoadingSkeleton count={4} height="180px" />
        ) : metrics ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-10">
            <KPICard
              title="Model Accuracy"
              value={`${(metrics.model?.accuracy * 100).toFixed(2)}%`}
              subtitle={`v${metrics.model?.version || 'N/A'}`}
              icon={FiCheckCircle}
              gradient={medicalTheme.colors.gradients.success_gradient}
            />
            
            <KPICard
              title="Model Drift"
              value={`${metrics.drift?.accuracy_drop_percentage?.toFixed(2) || '0.00'}%`}
              subtitle={driftStatus?.label}
              icon={FiTrendingDown}
              gradient={driftStatus?.gradient || medicalTheme.colors.gradients.warning_gradient}
              isAlert={metrics.drift?.detected}
              isPulsing={metrics.drift?.detected}
            />
            
            <KPICard
              title="Risk Score"
              value={metrics.risk?.latest_score?.toFixed(4) || '0.0000'}
              subtitle={`Trend: ${metrics.risk?.trend || 'N/A'}`}
              icon={FiActivity}
              gradient={medicalTheme.colors.gradients.forecast_gradient}
            />
            
            <KPICard
              title="Alert Status"
              value={metrics.risk?.current_severity || 'NORMAL'}
              subtitle={
                metrics.alerts?.latest?.created_at 
                  ? new Date(metrics.alerts.latest.created_at).toLocaleDateString()
                  : 'No alerts'
              }
              icon={FiAlertTriangle}
              gradient={
                metrics.risk?.current_severity === 'CRITICAL'
                  ? medicalTheme.colors.gradients.danger_gradient
                  : medicalTheme.colors.gradients.warning_gradient
              }
              isAlert={metrics.risk?.current_severity === 'CRITICAL'}
              isPulsing={metrics.risk?.current_severity === 'CRITICAL'}
            />
          </div>
        ) : null}

        {/* AI Diagnostics Section */}
        {metrics && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-10 items-stretch">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="h-full"
            >
              <TriageConfidenceRadar patients={patients} />
            </motion.div>
            
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="h-full"
            >
              <AnomalyRadarPulse driftData={metrics.drift} />
            </motion.div>
          </div>
        )}

        {/* Alert History */}
        {metrics?.alerts?.history_7_days && metrics.alerts.history_7_days.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-10">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
              className="lg:col-span-2"
            >
              <PremiumCard title="Alert History (7 Days)" subtitle="Trend analysis">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={metrics.alerts.history_7_days}>
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
                      dataKey="risk_score"
                      stroke={medicalTheme.colors.primary}
                      name="Risk Score"
                      strokeWidth={3}
                      dot={{ fill: medicalTheme.colors.primary, r: 5 }}
                      activeDot={{ r: 7 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </PremiumCard>
            </motion.div>
          </div>
        ) : null}

        {/* Diagnosis Distribution - Full Width */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.45 }}
          className="mb-10"
        >
          <SymptomDistributionVisualization patients={patients} />
        </motion.div>

        {/* Patient Entry Form */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="mb-10"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-800">Patient Submission</h2>
            <button
              onClick={() => setShowPatientForm((prev) => !prev)}
              className="btn-premium"
              style={{
                background: medicalTheme.colors.gradients.primary_gradient,
                color: 'white'
              }}
            >
              {showPatientForm ? 'Close Form' : 'Submit Patient'}
            </button>
          </div>
          {showPatientForm && (
            <PatientForm onSuccess={handlePatientSubmitted} />
          )}
        </motion.div>

        {/* Patient Records */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.6 }}
        >
          <PremiumCard title="Patient Records" subtitle={`${patients.length} total records`}>
            {patients.length === 0 ? (
              <EmptyState
                title="No Patient Records Yet"
                description="Start by submitting patient data to begin tracking clinical metrics."
                icon={FiUsers}
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gradient-to-r from-yellow-50 to-amber-50 border-b" style={{ borderColor: medicalTheme.colors.primary + '40' }}>
                    <tr>
                      <th className="px-4 py-3 text-left font-semibold text-gray-900">Age</th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-900">Gender</th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-900">Symptoms</th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-900">Diagnosis</th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-900">WBC Count</th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-900">Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {patients.slice(0, 20).map((patient, idx) => (
                      <motion.tr
                        key={idx}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: idx * 0.05 }}
                        className="border-b hover:bg-blue-50/50 transition-colors"
                        style={{ borderColor: medicalTheme.colors.primary + '10' }}
                      >
                        <td className="px-4 py-3 text-gray-700">{patient.age}</td>
                        <td className="px-4 py-3 text-gray-700">{patient.gender}</td>
                        <td className="px-4 py-3 text-gray-700">
                          {[patient.fever && '🌡️ Fever', patient.cough && '🫁 Cough', patient.headache && '🤕 Headache', patient.fatigue && '😴 Fatigue'].filter(Boolean).join(', ') || 'None'}
                        </td>
                        <td className="px-4 py-3 text-gray-700">{patient.disease_label}</td>
                        <td className="px-4 py-3 text-gray-700">{patient.wbc_count}</td>
                        <td className="px-4 py-3 text-gray-700">{new Date(patient.created_at).toLocaleDateString()}</td>
                      </motion.tr>
                    ))}
                  </tbody>
                </table>
                {patients.length > 20 && (
                  <p className="text-sm text-gray-600 mt-4 py-2 text-center">
                    Showing 20 of {patients.length} records
                  </p>
                )}
              </div>
            )}
          </PremiumCard>
        </motion.div>
      </div>
    </div>
  );
}
