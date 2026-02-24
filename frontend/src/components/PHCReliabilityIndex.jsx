import React, { useMemo } from 'react';
import { medicalTheme, getDriftStatus } from './MedicalTheme';
import { FiCheckCircle, FiAlertCircle, FiTrendingUp, FiTrendingDown } from 'react-icons/fi';

/**
 * PHC Reliability Index Cards
 * Shows status cards for each PHC with stability metrics
 * 
 * Data source: phc_breakdown from admin dashboard
 */
export default function PHCReliabilityIndex({ phcBreakdown = [] }) {
  const cards = useMemo(() => {
    return phcBreakdown.map(phc => {
      // Determine reliability status based on thresholds
      // API returns: phc_id, local_model_accuracy, risk_score, severity, patients
      const accuracy = phc.local_model_accuracy || 0;
      const riskScore = phc.risk_score || 0;
      const patientCount = phc.patients || 0;
      
      let status = 'Stable';
      let color = '#10B981'; // Green
      
      // Use risk score and severity from API
      if (phc.severity === 'CRITICAL') {
        status = 'Risk';
        color = '#EF4444'; // Red
      } else if (phc.severity === 'HIGH') {
        status = 'Volatile';
        color = '#F59E0B'; // Orange
      } else if (phc.severity === 'MEDIUM') {
        status = 'Caution';
        color = '#F59E0B'; // Orange
      } else if (accuracy > 0.85 && riskScore < 0.3) {
        status = 'Optimal';
        color = '#06B6D4'; // Cyan
      }

      return {
        name: phc.phc_id || 'Unknown PHC',
        status,
        color,
        accuracy: (accuracy * 100).toFixed(1),
        drift: (riskScore * 100).toFixed(1),
        patientCount,
        severity: phc.severity,
        trend: riskScore < 0.3 ? 'positive' : riskScore < 0.6 ? 'neutral' : 'negative'
      };
    });
  }, [phcBreakdown]);

  if (cards.length === 0) {
    return (
      <div 
        className="rounded-xl shadow-md p-8 border text-center"
        style={{
          background: `linear-gradient(135deg, ${medicalTheme.colors.primary}08 0%, ${medicalTheme.colors.secondary}08 100%)`,
          borderColor: medicalTheme.colors.primary + '30'
        }}
      >
        <p className="text-gray-500">No PHC data available</p>
      </div>
    );
  }

  return (
    <div 
      className="rounded-xl shadow-md p-6 border"
      style={{
        background: `linear-gradient(135deg, ${medicalTheme.colors.primary}08 0%, ${medicalTheme.colors.secondary}08 100%)`,
        borderColor: medicalTheme.colors.primary + '30'
      }}
    >
      <h3 className="text-lg font-semibold mb-6" style={{ color: medicalTheme.colors.primary }}>
        🏥 PHC Reliability Index
      </h3>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((card, idx) => (
          <div
            key={idx}
            className="rounded-lg border-l-4 shadow hover:shadow-lg transition-shadow p-4"
            style={{ 
              borderColor: card.color,
              background: card.color + '08'
            }}
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
              <h4 className="font-semibold text-gray-800 text-sm">{card.name}</h4>
              {card.status === 'Optimal' && <FiCheckCircle size={18} color={card.color} />}
              {card.status === 'Risk' && <FiAlertCircle size={18} color={card.color} />}
            </div>

            {/* Status Badge */}
            <div className="mb-3">
              <span 
                className="inline-block px-3 py-1 rounded-full text-xs font-semibold"
                style={{
                  background: card.color + '20',
                  color: card.color
                }}
              >
                {card.status}
              </span>
            </div>

            {/* Metrics */}
            <div className="space-y-2 text-sm mb-4">
              <div className="flex justify-between">
                <span className="text-gray-600">Accuracy</span>
                <span className="font-semibold" style={{ color: medicalTheme.colors.primary }}>
                  {card.accuracy}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Drift</span>
                <span 
                  className="font-semibold flex items-center gap-1"
                  style={{ color: card.color }}
                >
                  {card.drift}%
                  {card.trend === 'positive' && <FiTrendingDown size={14} className="text-green-600" />}
                  {card.trend === 'negative' && <FiTrendingUp size={14} className="text-red-600" />}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Patients</span>
                <span className="font-semibold text-gray-700">
                  {card.patientCount}
                </span>
              </div>
            </div>

            {/* Health Bar */}
            <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
              <div
                className="h-full transition-all duration-300 rounded-full"
                style={{
                  width: `${Math.min(parseFloat(card.accuracy), 100)}%`,
                  background: `linear-gradient(90deg, ${card.color}, ${card.color}80)`
                }}
              ></div>
            </div>

            {/* Recommendation */}
            {card.patientCount === 0 && (
              <p className="text-xs mt-3 p-2 rounded" style={{ background: '#94a3b8', color: '#f8fafc' }}>
                ⏳ Awaiting patient data
              </p>
            )}
            {card.status === 'Risk' && card.patientCount > 0 && (
              <p className="text-xs mt-3 p-2 rounded" style={{ background: card.color + '15', color: card.color }}>
                ⚠️ Requires attention
              </p>
            )}
            {card.status === 'Volatile' && card.patientCount > 0 && (
              <p className="text-xs mt-3 p-2 rounded" style={{ background: card.color + '15', color: card.color }}>
                🔄 Monitor closely
              </p>
            )}
          </div>
        ))}
      </div>

      {/* Summary Stats */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <p className="text-xs font-semibold text-gray-500 mb-3">NETWORK SUMMARY</p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3 bg-gray-50 rounded text-center">
            <p className="text-xs text-gray-600">PHCs Active</p>
            <p className="text-lg font-bold" style={{ color: medicalTheme.colors.primary }}>
              {cards.length}
            </p>
          </div>
          <div className="p-3 bg-gray-50 rounded text-center">
            <p className="text-xs text-gray-600">Optimal</p>
            <p className="text-lg font-bold text-green-600">
              {cards.filter(c => c.status === 'Optimal').length}
            </p>
          </div>
          <div className="p-3 bg-gray-50 rounded text-center">
            <p className="text-xs text-gray-600">Stable</p>
            <p className="text-lg font-bold" style={{ color: medicalTheme.colors.secondary }}>
              {cards.filter(c => c.status === 'Stable').length}
            </p>
          </div>
          <div className="p-3 bg-gray-50 rounded text-center">
            <p className="text-xs text-gray-600">At Risk</p>
            <p className="text-lg font-bold text-red-600">
              {cards.filter(c => c.status === 'Risk').length}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
