import React from 'react';
import { ShieldCheck, Leaf, Heart, Globe, Award } from 'lucide-react';
import { cn } from '../../lib/utils';
import type { PopStatus, PointOfParity } from '../../types';

type TrustMarkMatrixProps = {
  popStatus: PopStatus[];
  pointsOfParity: PointOfParity[];
};

const icons: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  organic_cert: Leaf,
  no_added_sugar: Heart,
  vegan_claim: Leaf,
  origin_claim: Globe,
  nutri_score: Award,
};

/**
 * Displays trust marks / points of parity with their status.
 */
export function TrustMarkMatrix({ popStatus, pointsOfParity }: TrustMarkMatrixProps) {
  const popNames: Record<string, string> = Object.fromEntries(
    pointsOfParity.map((p) => [p.pop_id, p.pop_name])
  );

  return (
    <div className="grid grid-cols-1 gap-2">
      {popStatus.map((pop) => {
        const Icon = icons[pop.pop_id] || ShieldCheck;
        return (
          <div
            key={pop.pop_id}
            className={cn(
              'flex items-start gap-3 p-3 rounded-xl border transition-all backdrop-blur-sm',
              pop.has_attribute
                ? 'bg-green-50/60 border-green-100/60 hover:bg-green-100/40'
                : 'bg-white/30 border-white/40 opacity-50 hover:opacity-70'
            )}
          >
            <div className={cn(
               'p-1.5 rounded-lg',
               pop.has_attribute ? 'bg-green-100/50 text-green-600' : 'bg-gray-100/30 text-gray-400'
            )}>
               <Icon size={16} />
            </div>
            
            <div className="flex-1 min-w-0 pt-0.5">
              <div
                className={cn(
                  'text-sm font-semibold',
                  pop.has_attribute ? 'text-gray-800' : 'text-gray-500'
                )}
              >
                {popNames[pop.pop_id] || pop.pop_id.replace(/_/g, ' ')}
              </div>
              {pop.has_attribute && pop.evidence && (
                <div className="text-xs text-gray-500 mt-1 leading-relaxed">{pop.evidence}</div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
