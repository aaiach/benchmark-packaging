import React from 'react';
import {
  ShieldCheck,
  Leaf,
  Heart,
  Globe,
  Award,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import type { Product, PointOfParity } from '../../types';

type TopTrustMarkersProps = {
  products: Product[];
  pointsOfParity: PointOfParity[];
};

type PopCount = {
  pop_id: string;
  name: string;
  count: number;
  percentage: number;
};

// Icon mapping for POP types based on pop_id
const icons: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  organic_cert: Leaf,
  no_added_sugar: Heart,
  vegan_claim: Leaf,
  origin_claim: Globe,
  nutri_score: Award,
};

/**
 * Displays the Points of Parity (trust markers) across all products in a category.
 * Shows all POPs with count of how many products have each attribute.
 */
export function TopTrustMarkers({ products, pointsOfParity }: TopTrustMarkersProps) {
  // Count how many products have each POP
  const popCounts = React.useMemo(() => {
    const counts: PopCount[] = pointsOfParity.map((pop) => {
      const count = products.filter((product) =>
        product.pop_status.some((status) => status.pop_id === pop.pop_id && status.has_attribute)
      ).length;

      return {
        pop_id: pop.pop_id,
        name: pop.pop_name,
        count,
        percentage: products.length > 0 ? Math.round((count / products.length) * 100) : 0,
      };
    });

    // Sort by count descending
    return counts.sort((a, b) => b.count - a.count);
  }, [products, pointsOfParity]);

  if (popCounts.length === 0) {
    return (
      <div className="text-center py-4 text-gray-500 text-sm">
        Aucun point de parité défini
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {popCounts.map((pop) => {
        const Icon = icons[pop.pop_id] || ShieldCheck;
        const hasProducts = pop.count > 0;

        return (
          <div
            key={pop.pop_id}
            className={cn(
              'flex items-center gap-3 p-2.5 rounded-lg border transition-all',
              hasProducts
                ? 'bg-emerald-500/10 border-emerald-500/20'
                : 'bg-white/5 border-white/10 opacity-60'
            )}
          >
            {/* Icon */}
            <Icon
              size={18}
              className={cn(
                'flex-shrink-0',
                hasProducts ? 'text-emerald-400' : 'text-gray-500'
              )}
            />

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div
                className={cn(
                  'text-sm font-medium truncate',
                  hasProducts ? 'text-emerald-100' : 'text-gray-400'
                )}
              >
                {pop.name}
              </div>
            </div>

            {/* Stats */}
            <div className="flex-shrink-0 text-right">
              <div className={cn(
                'text-sm font-semibold',
                hasProducts ? 'text-white' : 'text-gray-500'
              )}>
                {pop.percentage}%
              </div>
              <div className="text-xs text-gray-500">{pop.count} produits</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
