import React from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from 'recharts';

type RadarDataPoint = {
  subject: string;
  A: number;
  fullMark: number;
};

type RadarChartWrapperProps = {
  data: RadarDataPoint[];
  name?: string;
  color?: string;
  fillOpacity?: number;
  height?: number;
};

/**
 * Reusable radar chart component.
 */
export function RadarChartWrapper({
  data,
  name = 'Value',
  color = '#818cf8', // Indigo-400 equivalent
  fillOpacity = 0.3,
  height = 280,
}: RadarChartWrapperProps) {
  return (
    <div style={{ height }} className="-ml-4 relative">
       {/* Background circle for depth */}
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-50/50 to-purple-50/50 rounded-full blur-3xl opacity-50 transform scale-75" />
      
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="75%" data={data}>
          <PolarGrid stroke="rgba(0,0,0,0.05)" />
          <PolarAngleAxis 
            dataKey="subject" 
            tick={{ fill: '#64748b', fontSize: 11, fontWeight: 500 }} 
          />
          <PolarRadiusAxis angle={30} domain={[0, 10]} tick={false} axisLine={false} />
          <Radar
            name={name}
            dataKey="A"
            stroke={color}
            strokeWidth={2}
            fill={color}
            fillOpacity={fillOpacity}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
