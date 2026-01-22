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
              'flex items-start gap-3 p-3 rounded-lg border transition-all',
              pop.has_attribute
                ? 'bg-green-500/10 border-green-500/20'
                : 'bg-white/5 border-white/10 opacity-50'
            )}
          >
            <Icon
              size={16}
              className={cn(
                'mt-0.5',
                pop.has_attribute ? 'text-green-400' : 'text-gray-500'
              )}
            />
            <div className="flex-1 min-w-0">
              <div
                className={cn(
                  'text-sm font-medium',
                  pop.has_attribute ? 'text-green-100' : 'text-gray-400'
                )}
              >
                {popNames[pop.pop_id] || pop.pop_id.replace(/_/g, ' ')}
              </div>
              {pop.has_attribute && pop.evidence && (
                <div className="text-xs text-gray-400 mt-0.5 truncate">{pop.evidence}</div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
