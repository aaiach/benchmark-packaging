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
    <div className="space-y-2">
      {displayColors.map((color, idx) => (
        <div key={idx} className="flex items-center gap-3 group">
          <div
            className="w-8 h-8 rounded-lg border border-white/20 shadow-sm flex-shrink-0"
            style={{ backgroundColor: color.hex_code }}
          />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-sm text-white font-medium">{color.color_name}</span>
              <span className="text-xs text-gray-500">{color.hex_code}</span>
            </div>
            {showDetails && (
              <div className="text-xs text-gray-400 truncate">{color.usage}</div>
            )}
          </div>
          <div className="text-xs text-gray-500 tabular-nums">{color.coverage_percentage}%</div>
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
    <div className="flex gap-1">
      {palette.slice(0, maxColors).map((color, idx) => (
        <div
          key={idx}
          className="w-4 h-4 rounded-full border border-white/20"
          style={{ backgroundColor: color.hex_code }}
          title={`${color.color_name} (${color.coverage_percentage}%)`}
        />
      ))}
    </div>
  );
}
