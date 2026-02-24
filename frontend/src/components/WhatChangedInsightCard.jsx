import React, { useMemo } from 'react';
import { medicalTheme } from './MedicalTheme';
import { FiTrendingUp, FiTrendingDown, FiMinus } from 'react-icons/fi';

/**
 * What Changed Insight Card
 * Shows dynamic trend analysis of patient cohort changes
 * 
 * Data source: patients array from backend
 */
export default function WhatChangedInsightCard({ patients = [], historicalPatients = null }) {
  // Calculate demographic and symptom trends
  const metrics = useMemo(() => {
    if (!patients || patients.length === 0) {
      return {
        averageAge: 0,
        feverRate: 0,
        coughRate: 0,
        rashRate: 0,
        averageWBC: 0,
        trends: []
      };
    }

    const current = {
      averageAge: (patients.reduce((sum, p) => sum + (p.age || 0), 0) / patients.length).toFixed(1),
      feverRate: ((patients.filter(p => p.fever).length / patients.length) * 100).toFixed(1),
      coughRate: ((patients.filter(p => p.cough).length / patients.length) * 100).toFixed(1),
      rashRate: ((patients.filter(p => p.rash).length / patients.length) * 100).toFixed(1),
      averageWBC: (patients.reduce((sum, p) => sum + (p.wbc_count || 0), 0) / patients.length).toFixed(0),
    };

    // If historical data provided, calculate changes
    let changes = [];
    if (historicalPatients && historicalPatients.length > 0) {
      const historical = {
        averageAge: patients.reduce((sum, p) => sum + (p.age || 0), 0) / patients.length,
        feverRate: (historicalPatients.filter(p => p.fever).length / historicalPatients.length) * 100,
        coughRate: (historicalPatients.filter(p => p.cough).length / historicalPatients.length) * 100,
        rashRate: (historicalPatients.filter(p => p.rash).length / historicalPatients.length) * 100,
        averageWBC: historicalPatients.reduce((sum, p) => sum + (p.wbc_count || 0), 0) / historicalPatients.length,
      };

      changes = [
        {
          label: 'Age Distribution',
          old: historical.averageAge.toFixed(1),
          new: current.averageAge,
          change: (current.averageAge - historical.averageAge).toFixed(1),
          unit: 'years'
        },
        {
          label: 'Fever Cases',
          old: historical.feverRate.toFixed(1),
          new: current.feverRate,
          change: (current.feverRate - historical.feverRate).toFixed(1),
          unit: '%'
        },
        {
          label: 'Cough Cases',
          old: historical.coughRate.toFixed(1),
          new: current.coughRate,
          change: (current.coughRate - historical.coughRate).toFixed(1),
          unit: '%'
        },
        {
          label: 'Rash Cases',
          old: historical.rashRate.toFixed(1),
          new: current.rashRate,
          change: (current.rashRate - historical.rashRate).toFixed(1),
          unit: '%'
        },
        {
          label: 'Avg WBC Count',
          old: historical.averageWBC.toFixed(0),
          new: current.averageWBC,
          change: (current.averageWBC - historical.averageWBC).toFixed(0),
          unit: 'cells/μL'
        }
      ];
    }

    return { ...current, trends: changes };
  }, [patients, historicalPatients]);

  const getTrendIcon = (change) => {
    const val = parseFloat(change);
    if (val > 0.5) return <FiTrendingUp size={18} className="text-orange-600" />;
    if (val < -0.5) return <FiTrendingDown size={18} className="text-green-600" />;
    return <FiMinus size={18} className="text-gray-400" />;
  };

  const getTrendColor = (change) => {
    const val = parseFloat(change);
    if (val > 2) return '#D97706'; // increase (orange)
    if (val < -2) return '#16A34A'; // decrease (green)
    return '#9CA3AF'; // neutral (gray)
  };

  return (
    <div 
      className="rounded-xl shadow-md p-6 border"
      style={{ 
        background: `linear-gradient(135deg, ${medicalTheme.colors.primary}08 0%, ${medicalTheme.colors.secondary}08 100%)`,
        borderColor: medicalTheme.colors.primary + '30'
      }}
    >
      <h3 className="text-lg font-semibold mb-4" style={{ color: medicalTheme.colors.primary }}>
        📊 Cohort Changes
      </h3>

      {metrics.trends.length > 0 ? (
        <div className="space-y-3">
          {metrics.trends.map((trend, idx) => (
            <div 
              key={idx}
              className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-3 flex-1">
                {getTrendIcon(trend.change)}
                <div>
                  <p className="text-sm font-medium text-gray-700">{trend.label}</p>
                  <p className="text-xs text-gray-500">
                    {trend.old}{trend.unit} → {trend.new}{trend.unit}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p 
                  className="text-sm font-semibold"
                  style={{ color: getTrendColor(trend.change) }}
                >
                  {parseFloat(trend.change) > 0 ? '+' : ''}{trend.change}{trend.unit}
                </p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-4 bg-gray-50 rounded-lg text-center">
          <p className="text-sm text-gray-600">
            Historical data not available. Changes will appear after next data update.
          </p>
        </div>
      )}

      {/* Current snapshot */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <p className="text-xs font-semibold text-gray-500 mb-2">CURRENT SNAPSHOT</p>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          <div className="p-2 bg-gray-50 rounded">
            <p className="text-xs text-gray-600">Avg Age</p>
            <p className="text-sm font-semibold" style={{ color: medicalTheme.colors.primary }}>
              {metrics.averageAge} y
            </p>
          </div>
          <div className="p-2 bg-gray-50 rounded">
            <p className="text-xs text-gray-600">Fever</p>
            <p className="text-sm font-semibold" style={{ color: medicalTheme.colors.primary }}>
              {metrics.feverRate}%
            </p>
          </div>
          <div className="p-2 bg-gray-50 rounded">
            <p className="text-xs text-gray-600">Cough</p>
            <p className="text-sm font-semibold" style={{ color: medicalTheme.colors.primary }}>
              {metrics.coughRate}%
            </p>
          </div>
          <div className="p-2 bg-gray-50 rounded">
            <p className="text-xs text-gray-600">Rash</p>
            <p className="text-sm font-semibold" style={{ color: medicalTheme.colors.primary }}>
              {metrics.rashRate}%
            </p>
          </div>
          <div className="p-2 bg-gray-50 rounded col-span-2 sm:col-span-1">
            <p className="text-xs text-gray-600">Avg WBC</p>
            <p className="text-sm font-semibold" style={{ color: medicalTheme.colors.primary }}>
              {metrics.averageWBC}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
