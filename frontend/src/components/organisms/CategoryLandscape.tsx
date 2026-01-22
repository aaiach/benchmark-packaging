import React from 'react';
import { Card } from '../atoms';
import { RadarChartWrapper } from '../molecules';
import type { Product } from '../../types';

type CategoryLandscapeProps = {
  products: Product[];
  axisDescriptions: Record<string, string>;
};

/**
 * Category landscape overview with radar chart and stats.
 */
export function CategoryLandscape({ products, axisDescriptions }: CategoryLandscapeProps) {
  // Calculate category averages
  const categoryAverages = Object.keys(axisDescriptions).map((axisId) => {
    const sum = products.reduce((acc, p) => {
      const score = p.pod_scores.find((s) => s.axis_id === axisId)?.score || 0;
      return acc + score;
    }, 0);
    return {
      subject: axisDescriptions[axisId],
      A: Math.round((sum / products.length) * 10) / 10,
      fullMark: 10,
    };
  });

  return (
    <Card className="grid md:grid-cols-3 gap-8 items-center">
      <div className="col-span-1">
        <h2 className="text-2xl font-bold mb-4">Paysage Catégoriel</h2>
        <p className="text-gray-300 mb-6 text-sm leading-relaxed">
          Scores de positionnement moyens sur les {products.length} produits analysés 
          dans la catégorie.
        </p>
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-3 bg-white/5 rounded-lg">
            <div className="text-3xl font-bold text-white">{products.length}</div>
            <div className="text-xs text-gray-500 uppercase">Produits</div>
          </div>
          <div className="text-center p-3 bg-white/5 rounded-lg">
            <div className="text-3xl font-bold text-white">
              {Object.keys(axisDescriptions).length}
            </div>
            <div className="text-xs text-gray-500 uppercase">Axes</div>
          </div>
        </div>
      </div>

      <div className="col-span-2">
        <RadarChartWrapper
          data={categoryAverages}
          name="Moyenne Catégorie"
          height={320}
          fillOpacity={0.3}
        />
      </div>
    </Card>
  );
}
