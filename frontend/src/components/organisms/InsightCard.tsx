import React from 'react';
import { cn } from '../../lib/utils';
import { Badge, Card } from '../atoms';
import type { StrategicInsight } from '../../types';

type InsightCardProps = {
  insight: StrategicInsight;
};

const typeStyles: Record<string, string> = {
  competitive_landscape: 'from-blue-50 to-indigo-50 border-blue-100',
  differentiation_opportunity: 'from-emerald-50 to-teal-50 border-emerald-100',
  visual_trend: 'from-violet-50 to-fuchsia-50 border-violet-100',
  positioning_gap: 'from-amber-50 to-orange-50 border-amber-100',
};

const typeLabels: Record<string, string> = {
  competitive_landscape: 'Paysage Concurrentiel',
  differentiation_opportunity: 'Opportunité de Différenciation',
  visual_trend: 'Tendance Visuelle',
  positioning_gap: 'Écart de Positionnement',
};

const badgeVariants: Record<string, any> = {
  competitive_landscape: 'info',
  differentiation_opportunity: 'success',
  visual_trend: 'warning', // using warning for purple-ish tone fallback or custom
  positioning_gap: 'warning',
};

/**
 * Card for displaying strategic insights.
 */
export function InsightCard({ insight }: InsightCardProps) {
  const style = typeStyles[insight.insight_type] || 'from-gray-50 to-slate-50 border-gray-100';
  const badgeVariant = badgeVariants[insight.insight_type] || 'default';

  return (
    <Card
      className={cn(
        'bg-gradient-to-br shadow-sm hover:shadow-md transition-all duration-300',
        style
      )}
    >
      <Badge variant={badgeVariant} className="mb-4 shadow-sm">
        {typeLabels[insight.insight_type] || insight.insight_type.replace(/_/g, ' ')}
      </Badge>
      <h4 className="text-lg font-bold text-gray-900 mb-3">{insight.title}</h4>
      <p className="text-sm text-gray-600 leading-relaxed mb-6">{insight.description}</p>
      
      {insight.affected_brands.length > 0 && (
        <div className="flex flex-wrap gap-2 pt-4 border-t border-black/5">
          {insight.affected_brands.map((brand) => (
            <span key={brand} className="text-xs bg-white/60 px-2.5 py-1 rounded-md text-gray-500 font-medium border border-white/50 shadow-sm">
              {brand}
            </span>
          ))}
        </div>
      )}
    </Card>
  );
}
