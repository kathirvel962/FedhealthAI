import React, { useMemo } from 'react';
import { medicalTheme } from './MedicalTheme';
import { FiTrendingUp, FiAlertTriangle, FiCheckCircle } from 'react-icons/fi';

/**
 * Silent Spread Detector
 * Detects gradual increases in symptom patterns that might indicate emerging outbreaks
 * 
 * Data source: alerts with historical data (30+ days)
 */
export default function SilentSpreadDetector({ alerts = [] }) {
  const spreadAnalysis = useMemo(() => {
    if (!alerts || alerts.length < 10) {
      return {
        diagnoses: [],
        overall: { detected: false, risk: 'LOW' }
      };
    }

    // Group alerts by diagnosis and analyze trends
    const diagnosisTimeline = {};
    
    alerts.forEach(alert => {
      const diagnosis = alert.diagnosis || 'Unknown';
      const dateKey = new Date(alert.timestamp || Date.now()).toISOString().split('T')[0];
      
      if (!diagnosisTimeline[diagnosis]) {
        diagnosisTimeline[diagnosis] = {};
      }
      
      diagnosisTimeline[diagnosis][dateKey] = 
        (diagnosisTimeline[diagnosis][dateKey] || 0) + 1;
    });

    // Calculate trends for each diagnosis
    const trends = Object.entries(diagnosisTimeline).map(([diagnosis, timeline]) => {
      const dates = Object.keys(timeline).sort();
      
      if (dates.length < 3) {
        return {
          diagnosis,
          trend: 0,
          detected: false,
          riskLevel: 'LOW',
          description: 'Insufficient data'
        };
      }

      // Calculate trend slope (linear regression)
      const values = dates.map(d => timeline[d]);
      const n = values.length;
      const xMean = (n - 1) / 2;
      const yMean = values.reduce((a, b) => a + b, 0) / n;
      
      let numerator = 0;
      let denominator = 0;
      
      values.forEach((y, i) => {
        numerator += (i - xMean) * (y - yMean);
        denominator += (i - xMean) * (i - xMean);
      });
      
      const slope = denominator === 0 ? 0 : numerator / denominator;
      
      // Detect if increasing
      const isIncreasing = slope > 0.5;
      const isRapid = slope > 2;
      
      let riskLevel = 'LOW';
      let detected = false;
      
      if (isRapid && values[values.length - 1] > 10) {
        riskLevel = 'CRITICAL';
        detected = true;
      } else if (isRapid || (isIncreasing && values[values.length - 1] > 5)) {
        riskLevel = 'HIGH';
        detected = true;
      } else if (isIncreasing && values[values.length - 1] > 3) {
        riskLevel = 'MEDIUM';
        detected = true;
      }

      return {
        diagnosis,
        trend: slope.toFixed(2),
        currentCount: values[values.length - 1],
        previousCount: values[values.length - 2] || 0,
        changePercent: values[values.length - 2] 
          ? (((values[values.length - 1] - values[values.length - 2]) / values[values.length - 2]) * 100).toFixed(0)
          : 100,
        detected,
        riskLevel,
        description: detected 
          ? `${diagnosis} cases trending ${riskLevel.toLowerCase()}`
          : `${diagnosis} cases stable`
      };
    });

    const detectedTrends = trends.filter(t => t.detected);
    const overallRisk = 
      detectedTrends.some(t => t.riskLevel === 'CRITICAL') ? 'CRITICAL' :
      detectedTrends.some(t => t.riskLevel === 'HIGH') ? 'HIGH' :
      detectedTrends.some(t => t.riskLevel === 'MEDIUM') ? 'MEDIUM' : 'LOW';

    return {
      diagnoses: trends.sort((a, b) => parseFloat(b.trend) - parseFloat(a.trend)),
      overall: {
        detected: detectedTrends.length > 0,
        risk: overallRisk,
        detectedCount: detectedTrends.length,
        totalDiagnoses: trends.length
      }
    };
  }, [alerts]);

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'CRITICAL': return '#EF4444';
      case 'HIGH': return '#F97316';
      case 'MEDIUM': return '#F59E0B';
      default: return '#10B981';
    }
  };

  const getRiskBgColor = (risk) => {
    return getRiskColor(risk) + '15';
  };

  return (
    <div 
      className="rounded-xl shadow-md p-6 border"
      style={{
        background: `linear-gradient(135deg, ${medicalTheme.colors.primary}08 0%, ${medicalTheme.colors.secondary}08 100%)`,
        borderColor: medicalTheme.colors.primary + '30'
      }}
    >
      <h3 className="text-lg font-semibold mb-6" style={{ color: medicalTheme.colors.primary }}>
        🔍 Silent Spread Detector
      </h3>

      {/* Overall Status */}
      <div 
        className="p-4 rounded-lg border-l-4 mb-6"
        style={{
          background: getRiskBgColor(spreadAnalysis.overall.risk),
          borderColor: getRiskColor(spreadAnalysis.overall.risk)
        }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {spreadAnalysis.overall.detected ? (
              <FiAlertTriangle 
                size={24}
                style={{ color: getRiskColor(spreadAnalysis.overall.risk) }}
              />
            ) : (
              <FiCheckCircle 
                size={24}
                style={{ color: getRiskColor(spreadAnalysis.overall.risk) }}
              />
            )}
            <div>
              <p 
                className="font-semibold"
                style={{ color: getRiskColor(spreadAnalysis.overall.risk) }}
              >
                {spreadAnalysis.overall.detected ? 'Potential Spread Detected' : 'No Spreading Patterns'}
              </p>
              <p className="text-sm text-gray-600 mt-1">
                {spreadAnalysis.overall.detectedCount} of {spreadAnalysis.overall.totalDiagnoses} diagnoses showing concerning trends
              </p>
            </div>
          </div>
          <span 
            className="px-4 py-2 rounded-full font-bold text-lg"
            style={{
              background: getRiskColor(spreadAnalysis.overall.risk) + '25',
              color: getRiskColor(spreadAnalysis.overall.risk)
            }}
          >
            {spreadAnalysis.overall.risk}
          </span>
        </div>
      </div>

      {/* Diagnosis trends */}
      <div className="space-y-3">
        <p className="text-xs font-semibold text-gray-500 mb-3">DIAGNOSIS TRENDS</p>
        
        {spreadAnalysis.diagnoses.filter(d => d.detected).length > 0 ? (
          <>
            {spreadAnalysis.diagnoses.filter(d => d.detected).map((diagnosis, idx) => (
              <div 
                key={idx}
                className="p-4 rounded-lg border-l-4 bg-white hover:shadow-sm transition-shadow"
                style={{
                  borderColor: getRiskColor(diagnosis.riskLevel)
                }}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <FiTrendingUp 
                        size={18}
                        style={{ color: getRiskColor(diagnosis.riskLevel) }}
                      />
                      <p className="font-semibold text-gray-800 flex-1">
                        {diagnosis.diagnosis}
                      </p>
                      <span 
                        className="px-3 py-1 rounded-full text-xs font-bold"
                        style={{
                          background: getRiskBgColor(diagnosis.riskLevel),
                          color: getRiskColor(diagnosis.riskLevel)
                        }}
                      >
                        {diagnosis.riskLevel}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">
                      {diagnosis.currentCount} cases today (↑ {diagnosis.changePercent}% from yesterday)
                    </p>
                  </div>
                </div>
                
                {/* Trend visualization */}
                <div className="mt-3">
                  <div className="flex justify-between text-xs text-gray-500 mb-2">
                    <span>Trend slope: {diagnosis.trend} cases/day</span>
                    <span>Projected: {(parseFloat(diagnosis.trend) * 7 + diagnosis.currentCount).toFixed(0)} cases in 7 days</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${Math.min(parseFloat(diagnosis.trend) * 10, 100)}%`,
                        background: getRiskColor(diagnosis.riskLevel)
                      }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </>
        ) : (
          <div className="p-4 bg-green-50 rounded-lg border border-green-200 text-center">
            <p className="text-sm text-green-700 font-medium">
              ✓ No concerning spread patterns detected
            </p>
            <p className="text-xs text-green-600 mt-1">
              All diagnoses remain stable
            </p>
          </div>
        )}

        {/* Stable diagnoses */}
        {spreadAnalysis.diagnoses.filter(d => !d.detected).length > 0 && (
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <p className="text-xs font-semibold text-gray-600 mb-2">
              Stable Diagnoses ({spreadAnalysis.diagnoses.filter(d => !d.detected).length})
            </p>
            <div className="flex flex-wrap gap-2">
              {spreadAnalysis.diagnoses.filter(d => !d.detected).slice(0, 5).map((diagnosis, idx) => (
                <span 
                  key={idx}
                  className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full"
                >
                  {diagnosis.diagnosis} ({diagnosis.currentCount})
                </span>
              ))}
              {spreadAnalysis.diagnoses.filter(d => !d.detected).length > 5 && (
                <span className="text-xs px-2 py-1 bg-gray-200 text-gray-600 rounded-full">
                  +{spreadAnalysis.diagnoses.filter(d => !d.detected).length - 5} more
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Recommendations */}
      {spreadAnalysis.overall.detected && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <p className="text-xs font-semibold text-gray-500 mb-3">RECOMMENDED ACTIONS</p>
          <div className="space-y-2">
            {spreadAnalysis.overall.risk === 'CRITICAL' && (
              <div className="p-3 bg-red-50 border-l-4 border-red-600 rounded">
                <p className="text-sm font-semibold text-red-700">🚨 Immediate action required</p>
                <p className="text-xs text-red-600 mt-1">Escalate to district health officers</p>
              </div>
            )}
            {['HIGH', 'CRITICAL'].includes(spreadAnalysis.overall.risk) && (
              <div className="p-3 bg-orange-50 border-l-4 border-orange-600 rounded">
                <p className="text-sm font-semibold text-orange-700">⚠️ Enhanced surveillance</p>
                <p className="text-xs text-orange-600 mt-1">Monitor daily updates, prepare response protocols</p>
              </div>
            )}
            {['MEDIUM', 'HIGH', 'CRITICAL'].includes(spreadAnalysis.overall.risk) && (
              <div className="p-3 bg-yellow-50 border-l-4 border-yellow-600 rounded">
                <p className="text-sm font-semibold text-yellow-700">📊 Detailed analysis</p>
                <p className="text-xs text-yellow-600 mt-1">Review patient demographics and patterns</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
