import React, { useMemo } from 'react';
import { medicalTheme } from './MedicalTheme';
import { FiAlertCircle, FiCheckCircle } from 'react-icons/fi';

/**
 * District Risk Heatmap
 * Grid-based PHC risk visualization showing severity distribution
 * 
 * Data source: phc_breakdown with severity_distribution data
 */
export default function DistrictRiskHeatmap({ phcBreakdown = [] }) {
  const heatmapData = useMemo(() => {
    if (!phcBreakdown || phcBreakdown.length === 0) {
      return { cells: [], stats: {} };
    }

    // Create grid cells for each PHC
    const cells = phcBreakdown.map(phc => {
      // Calculate overall risk from metrics
      const accuracy = phc.model?.accuracy || 0;
      const drift = phc.drift?.accuracy_drop_percentage || 0;
      const alertCount = phc.alert_count || 0;
      
      // Determine severity based on multiple factors
      let severity = 'LOW';
      let color = '#10B981'; // Green
      let severity_level = 1;
      
      // Check accuracy
      if (accuracy < 0.6) {
        severity = 'CRITICAL';
        color = '#DC2626';
        severity_level = 4;
      } else if (accuracy < 0.75) {
        severity = 'HIGH';
        color = '#EA580C';
        severity_level = 3;
      }
      
      // Check drift
      if (drift > 20) {
        severity = 'CRITICAL';
        color = '#DC2626';
        severity_level = 4;
      } else if (drift > 10) {
        severity = 'HIGH';
        color = '#EA580C';
        severity_level = Math.max(severity_level, 3);
      } else if (drift > 5) {
        severity = 'MEDIUM';
        color = '#FBBF24';
        severity_level = Math.max(severity_level, 2);
      }
      
      // Check alert volume
      if (alertCount > 50) {
        severity = 'HIGH';
        color = '#EA580C';
        severity_level = Math.max(severity_level, 3);
      } else if (alertCount > 20) {
        severity = 'MEDIUM';
        color = '#FBBF24';
        severity_level = Math.max(severity_level, 2);
      }

      // Calculate risk percentage (0-100)
      const riskScore = Math.round(
        (Math.max(0, accuracy) * 0) + // Lower accuracy = higher risk
        (Math.min(drift / 25, 1) * 40) + // Drift contributes 40%
        (Math.min(alertCount / 100, 1) * 60) // Alert volume contributes 60%
      );

      return {
        phcId: phc._id || 'Unknown',
        phcName: phc.name || phc._id || 'Unknown',
        severity,
        severity_level,
        color,
        riskScore: Math.min(100, riskScore),
        accuracy: (accuracy * 100).toFixed(1),
        drift: drift.toFixed(1),
        alerts: alertCount,
        patients: phc.patient_count || 0
      };
    });

    // Calculate statistics
    const totalCells = cells.length;
    const criticalCount = cells.filter(c => c.severity === 'CRITICAL').length;
    const highCount = cells.filter(c => c.severity === 'HIGH').length;
    const mediumCount = cells.filter(c => c.severity === 'MEDIUM').length;
    const lowCount = cells.filter(c => c.severity === 'LOW').length;
    const avgRisk = (cells.reduce((sum, c) => sum + c.riskScore, 0) / totalCells).toFixed(1);

    return {
      cells: cells.sort((a, b) => b.riskScore - a.riskScore),
      stats: {
        total: totalCells,
        critical: criticalCount,
        high: highCount,
        medium: mediumCount,
        low: lowCount,
        avgRisk
      }
    };
  }, [phcBreakdown]);

  const getRiskLevel = (risk) => {
    if (risk >= 75) return 'CRITICAL';
    if (risk >= 50) return 'HIGH';
    if (risk >= 25) return 'MEDIUM';
    return 'LOW';
  };

  if (heatmapData.cells.length === 0) {
    return (
      <div 
        className="rounded-xl shadow-md p-8 border text-center"
        style={{
          background: `linear-gradient(135deg, ${medicalTheme.colors.primary}08 0%, ${medicalTheme.colors.secondary}08 100%)`,
          borderColor: medicalTheme.colors.primary + '30'
        }}
      >
        <p className="text-gray-500">No PHC data available for heatmap</p>
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
        🗺️ District Risk Heatmap
      </h3>

      {/* Heatmap Grid */}
      <div className={`grid gap-3 mb-6 ${
        heatmapData.cells.length === 1 ? 'grid-cols-1' :
        heatmapData.cells.length === 2 ? 'grid-cols-2' :
        heatmapData.cells.length === 3 ? 'grid-cols-3' :
        'grid-cols-2 sm:grid-cols-4'
      }`}>
        {heatmapData.cells.map((cell, idx) => (
          <div
            key={idx}
            className="p-4 rounded-lg border-2 shadow hover:shadow-lg transition-all cursor-pointer group relative overflow-hidden"
            style={{
              borderColor: cell.color,
              background: cell.color + '10'
            }}
          >
            {/* Background heatmap intensity */}
            <div
              className="absolute inset-0 opacity-20 transition-opacity group-hover:opacity-30"
              style={{
                background: `radial-gradient(circle, ${cell.color}80 0%, ${cell.color}20 100%)`
              }}
            ></div>

            {/* Content */}
            <div className="relative z-10">
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <p className="font-bold text-gray-800 text-sm truncate">
                    {cell.phcName}
                  </p>
                  <p className="text-xs text-gray-600">PHC</p>
                </div>
                {cell.severity === 'CRITICAL' && (
                  <FiAlertCircle size={20} style={{ color: cell.color }} />
                )}
                {cell.severity === 'LOW' && (
                  <FiCheckCircle size={20} style={{ color: cell.color }} />
                )}
              </div>

              {/* Risk Score Indicator */}
              <div className="mb-3">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-semibold text-gray-600">Risk Level</span>
                  <span 
                    className="px-2 py-1 rounded-full text-xs font-bold"
                    style={{
                      background: cell.color + '25',
                      color: cell.color
                    }}
                  >
                    {cell.severity}
                  </span>
                </div>
                <div className="relative w-full h-3 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full transition-all duration-300 rounded-full"
                    style={{
                      width: `${cell.riskScore}%`,
                      background: `linear-gradient(90deg, ${cell.color}, ${cell.color}80)`
                    }}
                  ></div>
                </div>
                <p className="text-xs text-gray-700 font-bold mt-2">
                  {cell.riskScore.toFixed(0)}%
                </p>
              </div>

              {/* Metrics */}
              <div className="space-y-1 text-xs">
                <div className="flex justify-between text-gray-600">
                  <span>Accuracy</span>
                  <span className="font-semibold text-gray-800">{cell.accuracy}%</span>
                </div>
                <div className="flex justify-between text-gray-600">
                  <span>Drift</span>
                  <span className="font-semibold text-gray-800">{cell.drift}%</span>
                </div>
                <div className="flex justify-between text-gray-600">
                  <span>Alerts</span>
                  <span className="font-semibold text-gray-800">{cell.alerts}</span>
                </div>
                <div className="flex justify-between text-gray-600">
                  <span>Patients</span>
                  <span className="font-semibold text-gray-800">{cell.patients}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="pt-6 border-t border-gray-200 mb-6">
        <p className="text-xs font-semibold text-gray-500 mb-3">RISK SCALE</p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded" style={{ background: '#10B981' }}></div>
            <div className="text-xs">
              <p className="font-semibold text-gray-700">Low</p>
              <p className="text-gray-500">0-25%</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded" style={{ background: '#FBBF24' }}></div>
            <div className="text-xs">
              <p className="font-semibold text-gray-700">Medium</p>
              <p className="text-gray-500">25-50%</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded" style={{ background: '#EA580C' }}></div>
            <div className="text-xs">
              <p className="font-semibold text-gray-700">High</p>
              <p className="text-gray-500">50-75%</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded" style={{ background: '#DC2626' }}></div>
            <div className="text-xs">
              <p className="font-semibold text-gray-700">Critical</p>
              <p className="text-gray-500">75-100%</p>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="pt-6 border-t border-gray-200">
        <p className="text-xs font-semibold text-gray-500 mb-3">DISTRICT SUMMARY</p>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          <div className="p-3 bg-gray-50 rounded text-center">
            <p className="text-xs text-gray-600 mb-1">Total PHCs</p>
            <p className="text-lg font-bold" style={{ color: medicalTheme.colors.primary }}>
              {heatmapData.stats.total}
            </p>
          </div>
          <div className="p-3 bg-gray-50 rounded text-center">
            <p className="text-xs text-gray-600 mb-1">Critical</p>
            <p className="text-lg font-bold text-red-600">
              {heatmapData.stats.critical}
            </p>
          </div>
          <div className="p-3 bg-gray-50 rounded text-center">
            <p className="text-xs text-gray-600 mb-1">High</p>
            <p className="text-lg font-bold text-orange-600">
              {heatmapData.stats.high}
            </p>
          </div>
          <div className="p-3 bg-gray-50 rounded text-center">
            <p className="text-xs text-gray-600 mb-1">Medium</p>
            <p className="text-lg font-bold text-yellow-600">
              {heatmapData.stats.medium}
            </p>
          </div>
          <div className="p-3 bg-gray-50 rounded text-center">
            <p className="text-xs text-gray-600 mb-1">Avg Risk</p>
            <p className="text-lg font-bold" style={{ color: medicalTheme.colors.secondary }}>
              {heatmapData.stats.avgRisk}%
            </p>
          </div>
        </div>
      </div>

      {/* Status Alert */}
      {heatmapData.stats.critical > 0 && (
        <div className="mt-4 p-4 bg-red-50 rounded-lg border-l-4 border-red-600">
          <p className="text-sm font-semibold text-red-700">🚨 Critical status detected</p>
          <p className="text-xs text-red-600 mt-1">
            {heatmapData.stats.critical} PHC{heatmapData.stats.critical !== 1 ? 's' : ''} require immediate attention
          </p>
        </div>
      )}

      {heatmapData.stats.critical === 0 && heatmapData.stats.high > 0 && (
        <div className="mt-4 p-4 bg-orange-50 rounded-lg border-l-4 border-orange-600">
          <p className="text-sm font-semibold text-orange-700">⚠️ High risk detected</p>
          <p className="text-xs text-orange-600 mt-1">
            {heatmapData.stats.high} PHC{heatmapData.stats.high !== 1 ? 's' : ''} showing high risk indicators
          </p>
        </div>
      )}

      {heatmapData.stats.critical === 0 && heatmapData.stats.high === 0 && (
        <div className="mt-4 p-4 bg-green-50 rounded-lg border-l-4 border-green-600">
          <p className="text-sm font-semibold text-green-700">✓ All PHCs stable</p>
          <p className="text-xs text-green-600 mt-1">
            District is operating within normal parameters
          </p>
        </div>
      )}
    </div>
  );
}
