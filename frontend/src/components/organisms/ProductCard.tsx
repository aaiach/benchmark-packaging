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
      className="group relative bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 rounded-xl p-4 transition-all duration-300 cursor-pointer flex flex-col h-full"
    >
      <div className="relative aspect-[3/4] mb-4 overflow-hidden rounded-lg bg-white/5">
        <img
          src={product.image}
          alt={product.name}
          className="w-full h-full object-contain p-2 transition-transform duration-500 group-hover:scale-105"
        />
      </div>

      <div className="mt-auto">
        <div className="text-xs text-blue-300 font-medium mb-1 uppercase tracking-wide">
          {product.brand}
        </div>
        <h3 className="text-sm font-semibold text-white leading-tight mb-2 line-clamp-2">
          {product.name}
        </h3>

        {/* Mini palette */}
        <div className="mb-2">
          <ColorPaletteCompact palette={product.palette} maxColors={4} />
        </div>

        <div className="flex flex-wrap gap-1">
          {product.pop_status
            .filter((p) => p.has_attribute)
            .slice(0, 2)
            .map((p) => (
              <span
                key={p.pop_id}
                className="text-[10px] px-1.5 py-0.5 bg-green-500/20 text-green-300 rounded"
              >
                {pointsOfParity.find((pop) => pop.pop_id === p.pop_id)?.pop_name.split(' ')[0] ||
                  p.pop_id.split('_')[0]}
              </span>
            ))}
          {product.pop_status.filter((p) => p.has_attribute).length > 2 && (
            <span className="text-[10px] px-1.5 py-0.5 bg-white/5 rounded text-gray-500">
              +{product.pop_status.filter((p) => p.has_attribute).length - 2}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
