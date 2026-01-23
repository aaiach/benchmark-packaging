import React from 'react';
import type { ColorEntry } from '../../types';

type ColorPaletteProps = {
  palette: ColorEntry[];
  maxColors?: number;
  showDetails?: boolean;
};

/**
 * Displays a color palette with coverage percentages.
 */
export function ColorPalette({ palette, maxColors = 5, showDetails = true }: ColorPaletteProps) {
  const displayColors = palette.slice(0, maxColors);

  return (
    <div className="space-y-3">
      {displayColors.map((color, idx) => (
        <div key={idx} className="flex items-center gap-3 group p-2 rounded-xl hover:bg-white/30 transition-colors">
          <div
            className="w-10 h-10 rounded-xl border border-white/40 shadow-sm flex-shrink-0"
            style={{ backgroundColor: color.hex_code }}
          />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-800 font-semibold">{color.color_name}</span>
              <span className="text-xs text-gray-500 font-mono bg-white/40 px-1.5 py-0.5 rounded-md border border-white/50">{color.hex_code}</span>
            </div>
            {showDetails && (
              <div className="text-xs text-gray-500 truncate mt-0.5">{color.usage}</div>
            )}
          </div>
          <div className="text-xs font-medium text-gray-600 tabular-nums bg-white/30 px-2 py-1 rounded-lg">{color.coverage_percentage}%</div>
        </div>
      ))}
    </div>
  );
}

/**
 * Compact color palette - just swatches.
 */
export function ColorPaletteCompact({ palette, maxColors = 4 }: { palette: ColorEntry[]; maxColors?: number }) {
  return (
    <div className="flex -space-x-1.5 hover:space-x-1 transition-all duration-300">
      {palette.slice(0, maxColors).map((color, idx) => (
        <div
          key={idx}
          className="w-5 h-5 rounded-full border border-white shadow-sm ring-1 ring-black/5"
          style={{ backgroundColor: color.hex_code }}
          title={`${color.color_name} (${color.coverage_percentage}%)`}
        />
      ))}
    </div>
  );
}
