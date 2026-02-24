import React, { useMemo } from 'react';
import { PieChart, Pie, Cell, Legend, Tooltip, ResponsiveContainer } from 'recharts';
import { medicalTheme } from './MedicalTheme';

/**
 * Symptom Distribution Visualization
 * Medical-styled pie/donut chart showing diagnosis distribution
 * 
 * Data source: patients array from backend
 */
export default function SymptomDistributionVisualization({ patients = [] }) {
  // Calculate diagnosis distribution
  const data = useMemo(() => {
    if (!patients || patients.length === 0) {
      return [];
    }

    const diagnoses = {};
    patients.forEach(patient => {
      const diagnosis = patient.disease_label || 'Unknown';
      diagnoses[diagnosis] = (diagnoses[diagnosis] || 0) + 1;
    });

    return Object.entries(diagnoses)
      .map(([name, count]) => ({
        name,
        value: count,
        percentage: ((count / patients.length) * 100).toFixed(1)
      }))
      .sort((a, b) => b.value - a.value);
  }, [patients]);

  // Medical color palette for diagnoses
  const colors = [
    medicalTheme.colors.primary,     // Blue
    medicalTheme.colors.secondary,   // Teal
    '#EF4444',                        // Red
    '#F97316',                        // Orange
    '#8B5CF6',                        // Purple
    '#EC4899',                        // Pink
    '#14B8A6',                        // Teal alt
    '#06B6D4',                        // Cyan
  ];

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div 
          className="p-3 rounded-lg shadow-lg border"
          style={{
            background: 'white',
            borderColor: payload[0].fill
          }}
        >
          <p className="font-semibold" style={{ color: payload[0].fill }}>
            {payload[0].name}
          </p>
          <p className="text-sm text-gray-600">
            {payload[0].payload.value} cases ({payload[0].payload.percentage}%)
          </p>
        </div>
      );
    }
    return null;
  };

  if (data.length === 0) {
    return (
      <div 
        className="rounded-xl shadow-md p-8 border flex items-center justify-center min-h-[300px]"
        style={{
          background: `linear-gradient(135deg, ${medicalTheme.colors.primary}08 0%, ${medicalTheme.colors.secondary}08 100%)`,
          borderColor: medicalTheme.colors.primary + '30'
        }}
      >
        <p className="text-gray-500">No diagnosis data available</p>
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
        🏥 Diagnosis Distribution
      </h3>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart */}
        <div className="lg:col-span-2">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={80}
                outerRadius={120}
                paddingAngle={2}
                dataKey="value"
              >
                {data.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={colors[index % colors.length]}
                    style={{
                      filter: `drop-shadow(0 2px 4px ${colors[index % colors.length]}40)`,
                    }}
                  />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend 
                layout="vertical"
                align="right"
                verticalAlign="middle"
                formatter={(value, entry) => (
                  <span style={{ fontSize: '12px', color: '#374151' }}>
                    {entry.payload.name}
                  </span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Statistics */}
        <div className="space-y-3">
          <p className="text-sm font-semibold text-gray-600 mb-4">BREAKDOWN</p>
          {data.map((item, idx) => (
            <div 
              key={idx}
              className="p-3 rounded-lg border-l-4 bg-white hover:shadow-sm transition-shadow"
              style={{ borderColor: colors[idx % colors.length] }}
            >
              <div className="flex justify-between items-start mb-1">
                <p className="text-sm font-medium text-gray-800">{item.name}</p>
                <span 
                  className="px-2 py-1 rounded text-xs font-semibold"
                  style={{
                    background: colors[idx % colors.length] + '15',
                    color: colors[idx % colors.length]
                  }}
                >
                  {item.percentage}%
                </span>
              </div>
              <p className="text-xs text-gray-500">{item.value} cases</p>
            </div>
          ))}
        </div>
      </div>

      {/* Summary */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <p className="text-xs font-semibold text-gray-500 mb-3">SUMMARY</p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3 bg-gray-50 rounded">
            <p className="text-xs text-gray-600">Total Cases</p>
            <p className="text-lg font-bold" style={{ color: medicalTheme.colors.primary }}>
              {patients.length}
            </p>
          </div>
          <div className="p-3 bg-gray-50 rounded">
            <p className="text-xs text-gray-600">Diagnoses</p>
            <p className="text-lg font-bold" style={{ color: medicalTheme.colors.secondary }}>
              {data.length}
            </p>
          </div>
          <div className="p-3 bg-gray-50 rounded">
            <p className="text-xs text-gray-600">Most Common</p>
            <p className="text-sm font-bold text-gray-800">{data[0]?.name || 'N/A'}</p>
          </div>
          <div className="p-3 bg-gray-50 rounded">
            <p className="text-xs text-gray-600">Coverage</p>
            <p className="text-lg font-bold" style={{ color: medicalTheme.colors.primary }}>
              100%
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
