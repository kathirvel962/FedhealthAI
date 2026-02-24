import React, { useMemo } from 'react';
import { medicalTheme } from './MedicalTheme';

/**
 * Cross-PHC Similarity Matrix
 * Heatmap showing disease distribution similarity between PHCs
 * 
 * Data source: phc_breakdown with alerts showing diagnosis patterns
 */
export default function CrossPHCSimilarityMatrix({ alerts = [], phcBreakdown = [] }) {
  const matrixData = useMemo(() => {
    if (!phcBreakdown || phcBreakdown.length === 0) {
      return { phcNames: [], matrix: [], diagnoses: [] };
    }

    // Extract diagnosis distribution by PHC
    const diagnosisByPHC = {};
    phcBreakdown.forEach(phc => {
      diagnosisByPHC[phc._id] = {};
    });

    // Count diagnoses in alerts
    if (alerts && alerts.length > 0) {
      alerts.forEach(alert => {
        const phc = alert.phc_id || 'Unknown';
        const diagnosis = alert.diagnosis || 'Unknown';
        
        if (diagnosisByPHC[phc]) {
          diagnosisByPHC[phc][diagnosis] = (diagnosisByPHC[phc][diagnosis] || 0) + 1;
        }
      });
    }

    const phcNames = Object.keys(diagnosisByPHC);
    
    // Get all unique diagnoses
    const allDiagnoses = new Set();
    Object.values(diagnosisByPHC).forEach(diagnoses => {
      Object.keys(diagnoses).forEach(d => allDiagnoses.add(d));
    });
    const diagnoses = Array.from(allDiagnoses).slice(0, 8); // Limit to 8 diagnoses

    // Calculate similarity matrix using Jaccard similarity
    // (shared diagnoses / total diagnoses)
    const matrix = phcNames.map((phc1, i) => {
      return phcNames.map((phc2, j) => {
        if (i === j) return 100; // Perfect similarity with self
        
        const diag1 = new Set(Object.keys(diagnosisByPHC[phc1]));
        const diag2 = new Set(Object.keys(diagnosisByPHC[phc2]));
        
        const intersection = new Set([...diag1].filter(x => diag2.has(x)));
        const union = new Set([...diag1, ...diag2]);
        
        const similarity = union.size === 0 ? 0 : (intersection.size / union.size) * 100;
        return Math.round(similarity);
      });
    });

    return { phcNames, matrix, diagnoses };
  }, [alerts, phcBreakdown]);

  const getColor = (similarity) => {
    // Red (dissimilar) → Yellow → Green (similar)
    if (similarity >= 80) return '#10B981'; // Green
    if (similarity >= 60) return '#84CC16'; // Lime
    if (similarity >= 40) return '#FBBF24'; // Amber
    if (similarity >= 20) return '#FB923C'; // Orange
    return '#EF4444'; // Red
  };

  const getTextColor = (similarity) => {
    return similarity >= 50 ? 'white' : '#374151';
  };

  if (matrixData.phcNames.length === 0) {
    return (
      <div 
        className="rounded-xl shadow-md p-8 border text-center"
        style={{
          background: `linear-gradient(135deg, ${medicalTheme.colors.primary}08 0%, ${medicalTheme.colors.secondary}08 100%)`,
          borderColor: medicalTheme.colors.primary + '30'
        }}
      >
        <p className="text-gray-500">Insufficient data for similarity matrix</p>
      </div>
    );
  }

  return (
    <div 
      className="rounded-xl shadow-md p-6 border overflow-x-auto"
      style={{
        background: `linear-gradient(135deg, ${medicalTheme.colors.primary}08 0%, ${medicalTheme.colors.secondary}08 100%)`,
        borderColor: medicalTheme.colors.primary + '30'
      }}
    >
      <h3 className="text-lg font-semibold mb-6" style={{ color: medicalTheme.colors.primary }}>
        🔗 Cross-PHC Disease Similarity Matrix
      </h3>

      {/* Matrix Table */}
      <div className="inline-block min-w-full">
        <div className="flex">
          {/* Row labels */}
          <div className="flex flex-col">
            <div className="w-32 h-12"></div>
            {matrixData.phcNames.map((phc, i) => (
              <div 
                key={i}
                className="w-32 h-12 flex items-center justify-center font-semibold text-sm text-gray-700 border-b border-gray-200 truncate px-2"
              >
                {phc}
              </div>
            ))}
          </div>

          {/* Matrix cells */}
          <div className="flex flex-col">
            {/* Column labels */}
            <div className="flex gap-0">
              {matrixData.phcNames.map((phc, i) => (
                <div 
                  key={i}
                  className="w-12 h-12 flex items-center justify-center font-semibold text-xs border border-gray-200 bg-gray-50 truncate"
                  title={phc}
                >
                  {phc.length > 3 ? phc.substring(0, 3) : phc}
                </div>
              ))}
            </div>

            {/* Data cells */}
            {matrixData.matrix.map((row, i) => (
              <div key={i} className="flex gap-0">
                {row.map((value, j) => (
                  <div
                    key={j}
                    className="w-12 h-12 flex items-center justify-center font-bold text-xs border border-gray-200 cursor-pointer hover:opacity-80 transition-opacity"
                    style={{
                      background: getColor(value),
                      color: getTextColor(value)
                    }}
                    title={`${matrixData.phcNames[i]} ↔ ${matrixData.phcNames[j]}: ${value}%`}
                  >
                    {value}%
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <p className="text-xs font-semibold text-gray-500 mb-3">SIMILARITY SCALE</p>
        <div className="flex flex-wrap gap-3">
          {[
            { label: 'Very Different', value: '&lt;20%', color: '#EF4444' },
            { label: 'Different', value: '20-40%', color: '#FB923C' },
            { label: 'Moderate', value: '40-60%', color: '#FBBF24' },
            { label: 'Similar', value: '60-80%', color: '#84CC16' },
            { label: 'Very Similar', value: '80-100%', color: '#10B981' },
          ].map((item, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <div
                className="w-6 h-6 rounded border border-gray-300"
                style={{ background: item.color }}
              ></div>
              <span className="text-xs text-gray-600">
                {item.label} ({item.value})
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Description */}
      <div className="mt-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
        <p className="text-xs text-blue-700">
          <strong>How to read:</strong> Matrix shows how similar disease patterns are between PHCs. 
          High values (green) indicate PHCs see similar diagnoses. Low values (red) indicate different disease patterns.
        </p>
      </div>

      {/* Interpretation */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="p-3 rounded-lg bg-green-50 border-l-4 border-green-600">
          <p className="text-xs font-semibold text-green-700 mb-1">🎯 High Similarity (80%+)</p>
          <p className="text-xs text-green-600">PHCs show similar disease patterns - federation is consistent</p>
        </div>
        <div className="p-3 rounded-lg bg-yellow-50 border-l-4 border-yellow-600">
          <p className="text-xs font-semibold text-yellow-700 mb-1">⚠️ Moderate (40-80%)</p>
          <p className="text-xs text-yellow-600">Some pattern variation - expected in federated system</p>
        </div>
        <div className="p-3 rounded-lg bg-red-50 border-l-4 border-red-600">
          <p className="text-xs font-semibold text-red-700 mb-1">🔴 Low Similarity (&lt;40%)</p>
          <p className="text-xs text-red-600">Very different patterns - may indicate data quality issues</p>
        </div>
      </div>
    </div>
  );
}
