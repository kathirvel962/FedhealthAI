import React, { useMemo } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { medicalTheme } from './MedicalTheme';

/**
 * Federation Strength Meter
 * Overall federation stability and health score (0-100)
 * 
 * Data sources:
 * - phc_breakdown (count of PHCs, stats per PHC)
 * - global_model metrics (drift, accuracy)
 */
export default function FederationStrengthMeter({ phcBreakdown = [], globalModel = {} }) {
  const strength = useMemo(() => {
    if (!phcBreakdown || phcBreakdown.length === 0) {
      return {
        score: 0,
        status: 'Initializing',
        color: '#9CA3AF',
        factors: []
      };
    }

    // Calculate stability components
    const phcCount = phcBreakdown.length;
    const phcDiversity = Math.min((phcCount / 4) * 100, 30); // Max 30% for having all 4 PHCs

    const accuracyScores = phcBreakdown
      .map(p => p.model?.accuracy || 0)
      .filter(a => a > 0);
    const avgAccuracy = accuracyScores.length > 0 
      ? (accuracyScores.reduce((a, b) => a + b, 0) / accuracyScores.length) * 100
      : 0;
    const accuracyHealth = Math.min(avgAccuracy, 50); // Max 50% for accuracy

    const driftScores = phcBreakdown
      .map(p => p.drift?.accuracy_drop_percentage || 0)
      .filter(d => d >= 0);
    const avgDrift = driftScores.length > 0 
      ? driftScores.reduce((a, b) => a + b, 0) / driftScores.length
      : 0;
    const driftHealth = Math.max(20 - Math.abs(avgDrift), 0); // Max 20%, penalize drift

    // Total: 30% diversity + 50% accuracy + 20% drift stability
    const totalScore = Math.round(phcDiversity + accuracyHealth + driftHealth);

    // Determine status
    let status = 'Initializing';
    let color = '#9CA3AF';
    if (totalScore >= 80) {
      status = 'Optimal';
      color = '#10B981';
    } else if (totalScore >= 60) {
      status = 'Stable';
      color = '#3B82F6';
    } else if (totalScore >= 40) {
      status = 'Volatile';
      color = '#F59E0B';
    } else {
      status = 'Critical';
      color = '#EF4444';
    }

    return {
      score: totalScore,
      status,
      color,
      factors: [
        {
          label: 'PHC Diversity',
          value: phcDiversity.toFixed(1),
          max: 30,
          unit: '%'
        },
        {
          label: 'Model Accuracy',
          value: accuracyHealth.toFixed(1),
          max: 50,
          unit: '%'
        },
        {
          label: 'Drift Stability',
          value: driftHealth.toFixed(1),
          max: 20,
          unit: '%'
        }
      ]
    };
  }, [phcBreakdown, globalModel]);

  const pieData = [
    { name: 'Strength', value: strength.score },
    { name: 'Remaining', value: 100 - strength.score }
  ];

  return (
    <div 
      className="rounded-xl shadow-md p-6 border"
      style={{
        background: `linear-gradient(135deg, ${strength.color}15 0%, ${strength.color}05 100%)`,
        borderColor: strength.color + '30'
      }}
    >
      <h3 className="text-lg font-semibold mb-6" style={{ color: medicalTheme.colors.primary }}>
        🔗 Federation Strength Meter
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Circular Meter */}
        <div className="flex flex-col items-center justify-center">
          <div className="relative w-48 h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={95}
                  startAngle={180}
                  endAngle={0}
                  dataKey="value"
                >
                  <Cell fill={strength.color} />
                  <Cell fill="#E5E7EB" />
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <p className="text-4xl font-bold" style={{ color: strength.color }}>
                {strength.score}
              </p>
              <p className="text-sm text-gray-600">/ 100</p>
            </div>
          </div>
          
          <div className="mt-6 text-center">
            <p 
              className="text-2xl font-bold"
              style={{ color: strength.color }}
            >
              {strength.status}
            </p>
            <p className="text-xs text-gray-500 mt-1">Federation Overall Health</p>
          </div>
        </div>

        {/* Factor Breakdown */}
        <div className="space-y-4">
          <p className="text-sm font-semibold text-gray-600 mb-4">HEALTH FACTORS</p>
          
          {strength.factors.map((factor, idx) => (
            <div key={idx} className="space-y-2">
              <div className="flex justify-between items-center">
                <p className="text-sm font-medium text-gray-700">{factor.label}</p>
                <span 
                  className="text-sm font-bold"
                  style={{ color: strength.color }}
                >
                  {factor.value} / {factor.max}{factor.unit}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
                <div
                  className="h-full transition-all duration-500 rounded-full"
                  style={{
                    width: `${(parseFloat(factor.value) / factor.max) * 100}%`,
                    background: `linear-gradient(90deg, ${strength.color}, ${strength.color}80)`
                  }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Status Indicators */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <p className="text-xs font-semibold text-gray-500 mb-3">STATUS INDICATORS</p>
        <div className="grid grid-cols-3 gap-3">
          <div className="p-3 bg-gray-50 rounded text-center">
            <p className="text-xs text-gray-600 mb-1">Contributing PHCs</p>
            <p className="text-lg font-bold" style={{ color: medicalTheme.colors.primary }}>
              {phcBreakdown.length}
            </p>
          </div>
          <div className="p-3 bg-gray-50 rounded text-center">
            <p className="text-xs text-gray-600 mb-1">Avg Accuracy</p>
            <p className="text-lg font-bold" style={{ color: medicalTheme.colors.secondary }}>
              {phcBreakdown.length > 0
                ? ((phcBreakdown.reduce((sum, p) => sum + (p.model?.accuracy || 0), 0) / phcBreakdown.length) * 100).toFixed(0)
                : 'N/A'}
              %
            </p>
          </div>
          <div className="p-3 bg-gray-50 rounded text-center">
            <p className="text-xs text-gray-600 mb-1">Status</p>
            <p 
              className="text-base font-bold"
              style={{ color: strength.color }}
            >
              {strength.status}
            </p>
          </div>
        </div>
      </div>

      {/* Health Recommendation */}
      {strength.score < 70 && (
        <div className="mt-4 p-4 rounded-lg" style={{ backgroundColor: strength.color + '15' }}>
          <p className="text-sm font-medium" style={{ color: strength.color }}>
            💡 Recommendation: Review PHC contributions and model accuracy to improve federation strength
          </p>
        </div>
      )}
    </div>
  );
}
