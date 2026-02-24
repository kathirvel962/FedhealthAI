import React, { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { medicalTheme } from './MedicalTheme';

/**
 * Drift Trend Over Time
 * Line chart showing drift progression across model versions
 * 
 * Data source: alerts with drift_detected and accuracy_drop_percentage
 */
export default function DriftTrendOverTime({ alerts = [] }) {
  const trendData = useMemo(() => {
    if (!alerts || alerts.length === 0) {
      return [];
    }

    // Group alerts by version and calculate average drift per version
    const versionMap = {};
    
    alerts.forEach(alert => {
      if (alert.drift_detected && alert.accuracy_drop_percentage) {
        const version = alert.model_version || 'v1';
        
        if (!versionMap[version]) {
          versionMap[version] = {
            driftValues: [],
            timestamp: alert.timestamp || new Date().toISOString(),
            count: 0
          };
        }
        
        versionMap[version].driftValues.push(alert.accuracy_drop_percentage);
        versionMap[version].count++;
      }
    });

    // Convert to chart format
    return Object.entries(versionMap)
      .map(([version, data]) => ({
        version,
        avgDrift: (data.driftValues.reduce((a, b) => a + b, 0) / data.driftValues.length).toFixed(2),
        maxDrift: Math.max(...data.driftValues).toFixed(2),
        minDrift: Math.min(...data.driftValues).toFixed(2),
        detections: data.count,
        timestamp: data.timestamp
      }))
      .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
  }, [alerts]);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div 
          className="p-3 rounded-lg shadow-lg bg-white border-2"
          style={{ borderColor: medicalTheme.colors.primary }}
        >
          <p className="font-semibold text-gray-800">{payload[0].payload.version}</p>
          <p className="text-sm text-gray-600">
            Avg Drift: {payload[0].value}%
          </p>
          <p className="text-xs text-gray-500">
            Detections: {payload[0].payload.detections}
          </p>
        </div>
      );
    }
    return null;
  };

  if (trendData.length === 0) {
    return (
      <div 
        className="rounded-xl shadow-md p-8 border text-center"
        style={{
          background: `linear-gradient(135deg, ${medicalTheme.colors.primary}08 0%, ${medicalTheme.colors.secondary}08 100%)`,
          borderColor: medicalTheme.colors.primary + '30'
        }}
      >
        <p className="text-gray-500">No drift trend data available</p>
      </div>
    );
  }

  // Calculate statistics
  const stats = useMemo(() => {
    const drifts = trendData.map(d => parseFloat(d.avgDrift));
    return {
      highestDrift: Math.max(...drifts).toFixed(2),
      lowestDrift: Math.min(...drifts).toFixed(2),
      averageDrift: (drifts.reduce((a, b) => a + b, 0) / drifts.length).toFixed(2),
      trend: drifts[drifts.length - 1] > drifts[0] ? 'increasing' : 'decreasing'
    };
  }, [trendData]);

  return (
    <div 
      className="rounded-xl shadow-md p-6 border"
      style={{
        background: `linear-gradient(135deg, ${medicalTheme.colors.primary}08 0%, ${medicalTheme.colors.secondary}08 100%)`,
        borderColor: medicalTheme.colors.primary + '30'
      }}
    >
      <h3 className="text-lg font-semibold mb-6" style={{ color: medicalTheme.colors.primary }}>
        📈 Model Drift Trend Over Time
      </h3>

      {/* Chart */}
      <div className="mb-6">
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={trendData}>
            <defs>
              <linearGradient id="colorDrift" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={medicalTheme.colors.primary} stopOpacity={0.3}/>
                <stop offset="95%" stopColor={medicalTheme.colors.primary} stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#D1D5DB" />
            <XAxis 
              dataKey="version"
              stroke="#6B7280"
              style={{ fontSize: '12px' }}
            />
            <YAxis 
              stroke="#6B7280"
              label={{ value: 'Drift %', angle: -90, position: 'insideLeft' }}
              style={{ fontSize: '12px' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Area 
              type="monotone" 
              dataKey="avgDrift" 
              stroke={medicalTheme.colors.primary}
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorDrift)"
              name="Avg Drift %"
              connectNulls
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Statistics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <div className="p-3 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-600 mb-1">Current Drift</p>
          <p className="text-lg font-bold" style={{ color: medicalTheme.colors.primary }}>
            {trendData[trendData.length - 1]?.avgDrift}%
          </p>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-600 mb-1">Highest Drift</p>
          <p className="text-lg font-bold text-orange-600">
            {stats.highestDrift}%
          </p>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-600 mb-1">Lowest Drift</p>
          <p className="text-lg font-bold text-green-600">
            {stats.lowestDrift}%
          </p>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-600 mb-1">Trend</p>
          <p className="text-lg font-bold" style={{ color: medicalTheme.colors.secondary }}>
            {stats.trend === 'increasing' ? '📈' : '📉'} {stats.trend}
          </p>
        </div>
      </div>

      {/* Version Details Table */}
      <div className="pt-6 border-t border-gray-200">
        <p className="text-xs font-semibold text-gray-500 mb-3">VERSION HISTORY</p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2 px-3 text-gray-600 font-semibold">Version</th>
                <th className="text-right py-2 px-3 text-gray-600 font-semibold">Avg Drift</th>
                <th className="text-right py-2 px-3 text-gray-600 font-semibold">Max Drift</th>
                <th className="text-right py-2 px-3 text-gray-600 font-semibold">Detections</th>
              </tr>
            </thead>
            <tbody>
              {trendData.map((item, idx) => (
                <tr 
                  key={idx}
                  className="border-b border-gray-100 hover:bg-gray-50"
                >
                  <td className="py-2 px-3 font-medium text-gray-800">{item.version}</td>
                  <td className="text-right py-2 px-3">
                    <span 
                      className="font-semibold"
                      style={{ color: parseFloat(item.avgDrift) > 10 ? '#F97316' : medicalTheme.colors.primary }}
                    >
                      {item.avgDrift}%
                    </span>
                  </td>
                  <td className="text-right py-2 px-3 text-orange-600 font-semibold">
                    {item.maxDrift}%
                  </td>
                  <td className="text-right py-2 px-3 text-gray-700">
                    <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs font-semibold">
                      {item.detections}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Status Message */}
      {stats.trend === 'increasing' && (
        <div className="mt-4 p-4 bg-orange-50 rounded-lg border-l-4 border-orange-600">
          <p className="text-sm font-medium text-orange-700">
            ⚠️ Drift is increasing. Models may be diverging from ground truth. Consider retraining.
          </p>
        </div>
      )}
      
      {stats.trend === 'decreasing' && (
        <div className="mt-4 p-4 bg-green-50 rounded-lg border-l-4 border-green-600">
          <p className="text-sm font-medium text-green-700">
            ✓ Drift is decreasing. Model quality is improving.
          </p>
        </div>
      )}
    </div>
  );
}
