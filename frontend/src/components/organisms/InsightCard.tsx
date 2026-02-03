import React, { useState } from 'react';
import { cn } from '../../lib/utils';
import { Badge, Card } from '../atoms';
import { ChevronDown, ChevronUp } from 'lucide-react';
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
 * Updated to be collapsible, cleaner, and more minimal.
 */
export function InsightCard({ insight }: InsightCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const style = typeStyles[insight.insight_type] || 'from-gray-50 to-slate-50 border-gray-100';
  const badgeVariant = badgeVariants[insight.insight_type] || 'default';

  return (
    <Card
      className={cn(
        'bg-gradient-to-br shadow-sm hover:shadow-md transition-all duration-300 overflow-hidden',
        style
      )}
    >
      <div 
        className="flex items-start justify-between gap-4 cursor-pointer select-none" 
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="space-y-3 flex-1">
          <Badge variant={badgeVariant} className="shadow-sm text-[10px] px-2 py-0.5 uppercase tracking-wider">
            {typeLabels[insight.insight_type] || insight.insight_type.replace(/_/g, ' ')}
          </Badge>
          <h4 className="text-base font-bold text-gray-900 leading-snug pr-2">
            {insight.title}
          </h4>
          {!isExpanded && (
             <p className="text-xs text-gray-500 line-clamp-2 leading-relaxed">
               {insight.description}
             </p>
          )}
        </div>
        <button 
          className="text-gray-400 hover:text-gray-600 transition-colors p-1 mt-1 flex-shrink-0"
          aria-label={isExpanded ? "Collapse" : "Expand"}
        >
          {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </button>
      </div>

      <div 
        className={cn(
          "grid transition-all duration-300 ease-in-out",
          isExpanded ? "grid-rows-[1fr] opacity-100 mt-4" : "grid-rows-[0fr] opacity-0 mt-0"
        )}
      >
        <div className="min-h-0 overflow-hidden">
          <p className="text-sm text-gray-700 leading-relaxed mb-4 border-t border-black/5 pt-4">
            {insight.description}
          </p>
          
          {insight.affected_brands.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {insight.affected_brands.map((brand) => (
                <span key={brand} className="text-[10px] bg-white/60 px-2 py-1 rounded-md text-gray-500 font-medium border border-white/50 shadow-sm">
                  {brand}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
