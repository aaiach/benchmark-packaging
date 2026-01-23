import React from 'react';
import { ColorPaletteCompact } from '../molecules/ColorPalette';
import type { Product, PointOfParity } from '../../types';

type ProductCardProps = {
  product: Product;
  onClick: () => void;
  pointsOfParity: PointOfParity[];
};

/**
 * Product card for the grid display.
 */
export function ProductCard({ product, onClick, pointsOfParity }: ProductCardProps) {
  return (
    <div
      onClick={onClick}
      className="glass-card group relative p-4 transition-all duration-300 cursor-pointer flex flex-col h-full hover:-translate-y-1 hover:shadow-glass-lg hover:bg-white/60"
    >
      <div className="relative aspect-[3/4] mb-4 overflow-hidden rounded-xl bg-white/40 border border-white/40 shadow-inner">
        <img
          src={product.image}
          alt={product.name}
          className="w-full h-full object-contain p-4 transition-transform duration-500 group-hover:scale-105 mix-blend-multiply"
        />
      </div>

      <div className="mt-auto">
        <div className="text-xs text-blue-600 font-bold mb-1.5 uppercase tracking-wide opacity-80">
          {product.brand}
        </div>
        <h3 className="text-sm font-bold text-gray-900 leading-tight mb-3 line-clamp-2 group-hover:text-blue-700 transition-colors">
          {product.name}
        </h3>

        {/* Mini palette */}
        <div className="mb-3">
          <ColorPaletteCompact palette={product.palette} maxColors={4} />
        </div>

        <div className="flex flex-wrap gap-1.5">
          {product.pop_status
            .filter((p) => p.has_attribute)
            .slice(0, 2)
            .map((p) => (
              <span
                key={p.pop_id}
                className="text-[10px] px-2 py-0.5 bg-emerald-100/60 text-emerald-700 rounded-md border border-emerald-200/50 font-medium"
              >
                {pointsOfParity.find((pop) => pop.pop_id === p.pop_id)?.pop_name.split(' ')[0] ||
                  p.pop_id.split('_')[0]}
              </span>
            ))}
          {product.pop_status.filter((p) => p.has_attribute).length > 2 && (
            <span className="text-[10px] px-2 py-0.5 bg-gray-100/60 rounded-md text-gray-500 font-medium border border-gray-200/50">
              +{product.pop_status.filter((p) => p.has_attribute).length - 2}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
