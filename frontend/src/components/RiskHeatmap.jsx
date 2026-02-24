import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { medicalTheme, getSeverityColor } from './MedicalTheme';

/**
 * Risk Level Heatmap Component
 * Visualizes risk distribution across cities and PHCs
 * Color intensity represents risk severity
 * 
 * City & PHC Structure:
 * - Pollachi: PHC_1, PHC_2
 * - Thondamuthur: PHC_3, PHC_4
 * - Kinathukadavu: PHC_5
 */
export default function RiskHeatmap({ riskData = null }) {
  const [heatmapData, setHeatmapData] = useState([]);
  const [hoveredCell, setHoveredCell] = useState(null);
  const [loading, setLoading] = useState(true);

  // Correct city-PHC mapping
  const cityPhcMapping = {
    'Pollachi': ['PHC_1', 'PHC_2'],
    'Thondamuthur': ['PHC_3', 'PHC_4'],
    'Kinathukadavu': ['PHC_5']
  };

  const cities = Object.keys(cityPhcMapping);
  const allPhcs = ['PHC_1', 'PHC_2', 'PHC_3', 'PHC_4', 'PHC_5'];

  useEffect(() => {
    // Generate heatmap data with correct city-PHC mapping
    const generateHeatmapData = () => {
      const data = cities.map((city) => {
        const phcsInCity = cityPhcMapping[city];
        
        return {
          city,
          phcsInCity, // Track which PHCs belong to this city
          phcRisks: phcsInCity.map((phc) => {
            // Simulated risk value (0-1)
            // In production, this would fetch actual risk scores from database
            const baseRisk = Math.random() * 0.8;
            return {
              phc,
              riskScore: baseRisk,
              patients: Math.floor(Math.random() * 1000) + 100,
              cases: Math.floor(Math.random() * 50) + 5
            };
          })
        };
      });
      setHeatmapData(data);
      setLoading(false);
    };

    if (!riskData) {
      generateHeatmapData();
    } else {
      setHeatmapData(riskData);
      setLoading(false);
    }
  }, []);

  /**
   * Get color for risk score
   * Golden gradient: Low (green) → Medium (yellow) → High (orange) → Critical (red)
   */
  const getRiskColor = (riskScore) => {
    if (riskScore < 0.35) {
      // LOW - Green
      return {
        bg: '#10B981',
        bgLight: '#ECFDF5',
        text: '#047857',
        label: 'LOW'
      };
    } else if (riskScore < 0.55) {
      // MEDIUM - Yellow/Gold
      return {
        bg: '#FFD700',
        bgLight: '#FFF9E1',
        text: '#CC9A00',
        label: 'MEDIUM'
      };
    } else if (riskScore < 0.75) {
      // HIGH - Orange
      return {
        bg: '#FFA500',
        bgLight: '#FFECCC',
        text: '#B87600',
        label: 'HIGH'
      };
    } else {
      // CRITICAL - Red
      return {
        bg: '#FF4444',
        bgLight: '#FFF0F0',
        text: '#CC0000',
        label: 'CRITICAL'
      };
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-yellow-400"></div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full"
    >
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-2xl font-bold bg-gradient-to-r from-yellow-600 to-orange-600 bg-clip-text text-transparent mb-2">
          Risk Distribution Heatmap
        </h3>
        <p className="text-gray-600 text-sm">
          Hovering shows exact risk scores. Color intensity represents health threat level.
        </p>
      </div>

      {/* Heatmap Container */}
      <div className="relative rounded-2xl overflow-hidden shadow-golden-lg border border-yellow-200/30 p-8 bg-gradient-to-br from-white to-yellow-50/30 backdrop-blur-sm">
        {/* Heatmap Grid */}
        <div className="overflow-x-auto">
          <div className="inline-block min-w-full">
            {/* Column Headers (PHCs) - Show all PHCs, but only render cells for PHCs in each city */}
        <div className="flex">
          <div className="w-32 flex-shrink-0"></div>
          {allPhcs.map((phc) => (
            <div
              key={`header-${phc}`}
              className="flex-1 min-w-32 text-center py-3 font-bold text-sm text-gray-700 border-b-2"
              style={{ borderColor: medicalTheme.colors.primary }}
            >
              {phc}
            </div>
          ))}
        </div>

        {/* Rows (Cities) with Risk Cells - Only show PHCs belonging to that city */}
        {heatmapData.map((row, rowIndex) => (
          <div key={`row-${row.city}`} className="flex">
            {/* Row Header (City) */}
            <div className="w-32 flex-shrink-0 py-4 px-4 font-bold text-sm text-gray-700 bg-gradient-to-r from-yellow-50 to-transparent border-r-2" style={{ borderColor: medicalTheme.colors.primary }}>
              {row.city}
            </div>

            {/* Risk Cells - Only for PHCs in this city */}
            {allPhcs.map((phc, colIndex) => {
              // Check if this PHC belongs to this city
              const phcInCity = row.phcRisks.find(p => p.phc === phc);
              const isHovered = hoveredCell?.row === rowIndex && hoveredCell?.col === colIndex;

              // If PHC doesn't belong to this city, render empty cell
              if (!phcInCity) {
                return (
                  <div
                    key={`cell-empty-${rowIndex}-${colIndex}`}
                    className="flex-1 min-w-32 p-3 transition-all duration-200"
                  >
                    <div className="w-full h-24 rounded-lg bg-gray-50/30"></div>
                  </div>
                );
              }

              const cell = phcInCity;
              const riskColor = getRiskColor(cell.riskScore);

              return (
                <motion.div
                  key={`cell-${rowIndex}-${colIndex}`}
                  whileHover={{ scale: 1.08 }}
                  onMouseEnter={() => setHoveredCell({ row: rowIndex, col: colIndex })}
                  onMouseLeave={() => setHoveredCell(null)}
                  className="flex-1 min-w-32 p-3 cursor-pointer transition-all duration-200 relative group"
                >
                  {/* Cell Background */}
                  <div
                    className={`w-full h-24 rounded-lg flex flex-col items-center justify-center text-center transition-all duration-300 ${
                      isHovered ? 'shadow-glow-golden-bright scale-105' : 'shadow-golden-md'
                    }`}
                    style={{
                      background: riskColor.bg,
                      opacity: 0.3 + (cell.riskScore * 0.7), // Higher risk = more opaque
                      border: isHovered ? `2px solid ${riskColor.text}` : `1px solid ${riskColor.bg}40`
                    }}
                  >
                    {/* Risk Score */}
                    <div className="text-lg font-black" style={{ color: riskColor.text }}>
                      {(cell.riskScore * 100).toFixed(0)}%
                    </div>
                    <div className="text-xs font-bold" style={{ color: riskColor.text }}>
                      {riskColor.label}
                    </div>
                  </div>

                  {/* Hover Tooltip */}
                  {isHovered && (
                    <motion.div
                      initial={{ opacity: 0, y: -5 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 bg-gray-900 text-white px-4 py-3 rounded-lg text-xs whitespace-nowrap z-50 shadow-xl"
                      style={{
                        boxShadow: `0 0 20px ${riskColor.bg}60`
                      }}
                    >
                      <div className="font-bold">{row.city} - {cell.phc}</div>
                      <div>Risk: {(cell.riskScore * 100).toFixed(1)}%</div>
                      <div>Patients: {cell.patients}</div>
                      <div>Cases: {cell.cases}</div>
                      <div className="text-yellow-300 font-semibold mt-1">{riskColor.label}</div>
                    </motion.div>
                  )}
                </motion.div>
              );
            })}
          </div>
        ))}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-8 flex flex-wrap gap-6 justify-center">
        <div className="flex items-center gap-3">
          <div
            className="w-6 h-6 rounded-md"
            style={{ backgroundColor: '#10B981', opacity: 0.8 }}
          ></div>
          <span className="text-sm font-semibold text-gray-700">LOW Risk</span>
        </div>
        <div className="flex items-center gap-3">
          <div
            className="w-6 h-6 rounded-md"
            style={{ backgroundColor: '#FFD700', opacity: 0.8 }}
          ></div>
          <span className="text-sm font-semibold text-gray-700">MEDIUM Risk</span>
        </div>
        <div className="flex items-center gap-3">
          <div
            className="w-6 h-6 rounded-md"
            style={{ backgroundColor: '#FFA500', opacity: 0.8 }}
          ></div>
          <span className="text-sm font-semibold text-gray-700">HIGH Risk</span>
        </div>
        <div className="flex items-center gap-3">
          <div
            className="w-6 h-6 rounded-md"
            style={{ backgroundColor: '#FF4444', opacity: 0.8 }}
          ></div>
          <span className="text-sm font-semibold text-gray-700">CRITICAL Risk</span>
        </div>
      </div>

      {/* Stats Section */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-4">
        {(() => {
          // Calculate stats from actual data
          const allRisks = heatmapData.flatMap(row => row.phcRisks.map(r => r.riskScore));
          const maxRisk = allRisks.length > 0 ? Math.max(...allRisks) : 0;
          const minRisk = allRisks.length > 0 ? Math.min(...allRisks) : 0;
          
          return [
            { label: 'Total PHCs', value: allPhcs.length, color: '#FFD700' },
            { label: 'Total Cities', value: cities.length, color: '#FFA500' },
            { label: 'Highest Risk', value: (maxRisk * 100).toFixed(1) + '%', color: '#FF4444' },
            { label: 'Lowest Risk', value: (minRisk * 100).toFixed(1) + '%', color: '#10B981' }
          ].map((stat, idx) => (
            <div
              key={idx}
              className="p-4 rounded-lg bg-white/70 border border-yellow-200/30 text-center"
              style={{
                boxShadow: `0 0 15px ${stat.color}30`
              }}
            >
              <div className="text-2xl font-bold" style={{ color: stat.color }}>
                {stat.value}
              </div>
              <div className="text-xs font-semibold text-gray-600 mt-1">{stat.label}</div>
            </div>
          ));
        })()}
      </div>
    </motion.div>
  );
}
