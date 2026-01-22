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
  color = '#3b82f6',
  fillOpacity = 0.4,
  height = 280,
}: RadarChartWrapperProps) {
  return (
    <div style={{ height }} className="-ml-4">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="75%" data={data}>
          <PolarGrid stroke="rgba(255,255,255,0.1)" />
          <PolarAngleAxis dataKey="subject" tick={{ fill: '#9ca3af', fontSize: 10 }} />
          <PolarRadiusAxis angle={30} domain={[0, 10]} tick={false} axisLine={false} />
          <Radar
            name={name}
            dataKey="A"
            stroke={color}
            fill={color}
            fillOpacity={fillOpacity}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
