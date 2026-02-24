import React, { useMemo } from 'react';
import { LineChart, Line, Area, AreaChart, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import { medicalTheme } from './MedicalTheme';
import { FiTrendingUp, FiTrendingDown } from 'react-icons/fi';

/**
 * Seven Day Risk Forecast
 * Simple linear regression forecast of risk scores for next 7 days
 * 
 * Data source: historical risk scores from alerts or metrics (7-30 days)
 */
export default function SevenDayRiskForecast({ historicalRisks = [], currentRisk = 0 }) {
  const forecastData = useMemo(() => {
    if (!historicalRisks || historicalRisks.length < 3) {
      return {
        chart: [],
        forecast: [],
        stats: { trend: 'unknown', projection: 0, confidence: 0 }
      };
    }

    // Sort historical by date
    const sorted = [...historicalRisks].sort((a, b) => {
      const dateA = a.date ? new Date(a.date) : new Date(a.timestamp || 0);
      const dateB = b.date ? new Date(b.date) : new Date(b.timestamp || 0);
      return dateA - dateB;
    });

    // Extract values for linear regression
    const values = sorted.map(d => d.risk || d.value || 0);
    const n = values.length;
    
    if (n < 2) {
      return {
        chart: [],
        forecast: [],
        stats: { trend: 'unknown', projection: 0, confidence: 0 }
      };
    }

    // Calculate linear regression
    const xMean = (n - 1) / 2;
    const yMean = values.reduce((a, b) => a + b, 0) / n;
    
    let numerator = 0;
    let denominator = 0;
    
    values.forEach((y, i) => {
      numerator += (i - xMean) * (y - yMean);
      denominator += (i - xMean) * (i - xMean);
    });
    
    const slope = denominator === 0 ? 0 : numerator / denominator;
    const intercept = yMean - slope * xMean;

    // Prepare chart data with historical + forecast
    const chartData = sorted.map((d, idx) => ({
      day: d.label || `Day ${idx - n + 1}`,
      actual: values[idx],
      forecast: null,
      type: 'historical'
    }));

    // Generate 7-day forecast
    const forecast = [];
    const today = new Date();
    
    for (let i = 1; i <= 7; i++) {
      const forecastDate = new Date(today);
      forecastDate.setDate(forecastDate.getDate() + i);
      
      const forecastIdx = n - 1 + i;
      const forecastValue = Math.max(0, Math.min(100, intercept + slope * forecastIdx));
      
      forecast.push({
        day: `+${i}d`,
        actual: null,
        forecast: forecastValue,
        type: 'forecast',
        date: forecastDate
      });
    }

    // Add current risk as reference
    if (currentRisk > 0) {
      chartData.push({
        day: 'Today',
        actual: currentRisk,
        forecast: null,
        type: 'current'
      });
    }

    // Calculate projection for 7 days
    const projection7d = Math.max(0, Math.min(100, intercept + slope * (n - 1 + 7)));
    
    // Calculate trend
    const trend = slope > 0.5 ? 'increasing' : slope < -0.5 ? 'decreasing' : 'stable';
    
    // Calculate R-squared for confidence
    let ssRes = 0;
    let ssTot = 0;
    values.forEach((y, i) => {
      const predicted = intercept + slope * i;
      ssRes += Math.pow(y - predicted, 2);
      ssTot += Math.pow(y - yMean, 2);
    });
    const rSquared = ssTot === 0 ? 0 : Math.max(0, 1 - ssRes / ssTot) * 100;

    return {
      chart: chartData,
      forecast: forecast,
      stats: {
        trend,
        projection: projection7d,
        confidence: rSquared,
        slope: slope.toFixed(2),
        current: values[values.length - 1]
      }
    };
  }, [historicalRisks, currentRisk]);

  const combined = useMemo(() => {
    return [...forecastData.chart, ...forecastData.forecast];
  }, [forecastData]);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="p-3 rounded-lg shadow-lg bg-white border-2" style={{ borderColor: medicalTheme.colors.primary }}>
          <p className="font-semibold text-gray-800">{data.day}</p>
          {data.actual !== null && (
            <p className="text-sm text-gray-600">
              Actual: <span className="font-semibold">{data.actual.toFixed(1)}%</span>
            </p>
          )}
          {data.forecast !== null && (
            <p className="text-sm text-orange-600">
              Forecast: <span className="font-semibold">{data.forecast.toFixed(1)}%</span>
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  if (combined.length === 0) {
    return (
      <div 
        className="rounded-xl shadow-md p-8 border text-center"
        style={{
          background: `linear-gradient(135deg, ${medicalTheme.colors.primary}08 0%, ${medicalTheme.colors.secondary}08 100%)`,
          borderColor: medicalTheme.colors.primary + '30'
        }}
      >
        <p className="text-gray-500">Insufficient historical data for forecast</p>
        <p className="text-xs text-gray-400 mt-1">Need at least 3 data points</p>
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
        📈 7-Day Risk Forecast
      </h3>

      {/* Forecast Chart */}
      <div className="mb-6">
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={combined}>
            <defs>
              <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={medicalTheme.colors.primary} stopOpacity={0.3}/>
                <stop offset="95%" stopColor={medicalTheme.colors.primary} stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#F97316" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#F97316" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#D1D5DB" />
            <XAxis 
              dataKey="day"
              stroke="#6B7280"
              style={{ fontSize: '12px' }}
            />
            <YAxis 
              stroke="#6B7280"
              domain={[0, 100]}
              label={{ value: 'Risk Score %', angle: -90, position: 'insideLeft' }}
              style={{ fontSize: '12px' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <ReferenceLine y={50} stroke="#E5E7EB" strokeDasharray="3 3" label="Moderate Risk" />
            
            {/* Historical area */}
            <Area 
              type="monotone" 
              dataKey="actual" 
              stroke={medicalTheme.colors.primary}
              strokeWidth={2}
              fill="url(#colorActual)"
              name="Actual Risk"
              connectNulls
              isAnimationActive={false}
            />
            
            {/* Forecast line */}
            <Line 
              type="monotone" 
              dataKey="forecast" 
              stroke="#F97316"
              strokeWidth={2}
              strokeDasharray="5 5"
              name="Forecast"
              connectNulls
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <div className="p-3 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-600 mb-1">Current Risk</p>
          <p className="text-lg font-bold" style={{ color: medicalTheme.colors.primary }}>
            {forecastData.stats.current?.toFixed(1) || 'N/A'}%
          </p>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-600 mb-1">7-Day Projection</p>
          <p className="text-lg font-bold text-orange-600">
            {forecastData.stats.projection?.toFixed(1) || 'N/A'}%
          </p>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-600 mb-1">Trend</p>
          <div className="flex items-center gap-1 mt-1">
            {forecastData.stats.trend === 'increasing' && (
              <>
                <FiTrendingUp size={18} className="text-red-600" />
                <span className="text-sm font-bold text-red-600">Rising</span>
              </>
            )}
            {forecastData.stats.trend === 'decreasing' && (
              <>
                <FiTrendingDown size={18} className="text-green-600" />
                <span className="text-sm font-bold text-green-600">Falling</span>
              </>
            )}
            {forecastData.stats.trend === 'stable' && (
              <span className="text-sm font-bold text-gray-600">Stable</span>
            )}
          </div>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-600 mb-1">Confidence</p>
          <p className="text-lg font-bold" style={{ color: medicalTheme.colors.secondary }}>
            {forecastData.stats.confidence?.toFixed(0) || 'N/A'}%
          </p>
        </div>
      </div>

      {/* Forecast Table */}
      <div className="pt-6 border-t border-gray-200">
        <p className="text-xs font-semibold text-gray-500 mb-3">7-DAY OUTLOOK</p>
        <div className="grid grid-cols-7 gap-2">
          {forecastData.forecast.map((item, idx) => (
            <div 
              key={idx}
              className="p-3 rounded-lg bg-white border-2 text-center hover:shadow-sm transition-shadow"
              style={{
                borderColor: item.forecast > 70 ? '#EF4444' : item.forecast > 50 ? '#F97316' : '#10B981'
              }}
            >
              <p className="text-xs font-bold text-gray-600 mb-1">{item.day}</p>
              <p 
                className="text-lg font-bold"
                style={{
                  color: item.forecast > 70 ? '#EF4444' : item.forecast > 50 ? '#F97316' : '#10B981'
                }}
              >
                {item.forecast.toFixed(0)}%
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {item.forecast > 70 ? '🔴' : item.forecast > 50 ? '🟠' : '🟢'}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Interpretation */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <p className="text-xs font-semibold text-gray-500 mb-3">FORECAST INTERPRETATION</p>
        
        {forecastData.stats.trend === 'increasing' && (
          <div className="p-4 bg-red-50 rounded-lg border-l-4 border-red-600">
            <p className="text-sm font-semibold text-red-700">⚠️ Risk is increasing</p>
            <p className="text-xs text-red-600 mt-1">
              Projected to reach {forecastData.stats.projection.toFixed(1)}% in 7 days. 
              Consider preventive interventions now.
            </p>
          </div>
        )}
        
        {forecastData.stats.trend === 'decreasing' && (
          <div className="p-4 bg-green-50 rounded-lg border-l-4 border-green-600">
            <p className="text-sm font-semibold text-green-700">✓ Risk is decreasing</p>
            <p className="text-xs text-green-600 mt-1">
              Projected to reach {forecastData.stats.projection.toFixed(1)}% in 7 days. 
              Current interventions appear effective.
            </p>
          </div>
        )}
        
        {forecastData.stats.trend === 'stable' && (
          <div className="p-4 bg-yellow-50 rounded-lg border-l-4 border-amber-600">
            <p className="text-sm font-semibold text-amber-700">➡️ Risk is stable</p>
            <p className="text-xs text-amber-600 mt-1">
              Expected to remain around {forecastData.stats.projection.toFixed(1)}% for next week. 
              Maintain current monitoring levels.
            </p>
          </div>
        )}

        <p className="text-xs text-gray-500 mt-3">
          📊 Confidence: {forecastData.stats.confidence?.toFixed(0)}% 
          (based on historical trend goodness-of-fit)
        </p>
      </div>
    </div>
  );
}
