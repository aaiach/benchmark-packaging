import React from 'react';
import { cn } from '../../lib/utils';
import { Badge, Card } from '../atoms';
import type { StrategicInsight } from '../../types';

type InsightCardProps = {
  insight: StrategicInsight;
};

const typeColors: Record<string, string> = {
  competitive_landscape: 'from-blue-500/20 to-cyan-500/20 border-blue-500/30',
  differentiation_opportunity: 'from-green-500/20 to-emerald-500/20 border-green-500/30',
  visual_trend: 'from-purple-500/20 to-pink-500/20 border-purple-500/30',
  positioning_gap: 'from-orange-500/20 to-yellow-500/20 border-orange-500/30',
};

/**
 * Card for displaying strategic insights.
 */
export function InsightCard({ insight }: InsightCardProps) {
  return (
    <Card
      className={cn(
        'bg-gradient-to-br',
        typeColors[insight.insight_type] || 'from-gray-500/20 to-gray-600/20'
      )}
    >
      <Badge variant="outline" className="mb-3">
        {insight.insight_type.replace(/_/g, ' ')}
      </Badge>
      <h4 className="text-lg font-semibold text-white mb-2">{insight.title}</h4>
      <p className="text-sm text-gray-300 leading-relaxed mb-4">{insight.description}</p>
      <div className="flex flex-wrap gap-1">
        {insight.affected_brands.map((brand) => (
          <span key={brand} className="text-xs bg-white/10 px-2 py-0.5 rounded text-gray-400">
            {brand}
          </span>
        ))}
      </div>
    </Card>
  );
}
