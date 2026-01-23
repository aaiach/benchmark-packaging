import React from 'react';
import { BarChart3, ShieldCheck, Package, Target } from 'lucide-react';
import { Card } from '../atoms';
import { RadarChartWrapper, TopTrustMarkers } from '../molecules';
import type { Product, PointOfParity } from '../../types';

type CategoryLandscapeProps = {
  products: Product[];
  axisDescriptions: Record<string, string>;
  pointsOfParity: PointOfParity[];
};

/**
 * Category landscape overview with radar chart, stats, and top trust markers.
 * Responsive layout: stacks vertically on mobile, side-by-side on desktop.
 */
export function CategoryLandscape({ products, axisDescriptions, pointsOfParity }: CategoryLandscapeProps) {
  const axisCount = Object.keys(axisDescriptions).length;

  // Calculate category averages for radar chart
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
    <Card className="p-0 overflow-hidden">
      {/* Header Section */}
      <div className="px-6 py-5 border-b border-white/10 bg-gradient-to-r from-white/5 to-transparent">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-white flex items-center gap-3">
              <BarChart3 className="text-blue-400" size={24} />
              Aperçu de la catégorie
            </h2>
            <p className="text-gray-400 text-sm mt-1">
              Analyse de positionnement sur {products.length} produits
            </p>
          </div>

          {/* Quick Stats Pills */}
          <div className="flex flex-wrap gap-2">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-full">
              <Package size={14} className="text-blue-400" />
              <span className="text-sm font-medium text-blue-200">{products.length} produits</span>
            </div>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-purple-500/10 border border-purple-500/20 rounded-full">
              <Target size={14} className="text-purple-400" />
              <span className="text-sm font-medium text-purple-200">{axisCount} axes</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="p-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8">
          
          {/* Radar Chart Section - Takes 7 columns on large screens */}
          <div className="lg:col-span-7 order-2 lg:order-1">
            <div className="bg-white/[0.02] rounded-xl p-4 border border-white/5">
              <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wide mb-4">
                Positionnement moyen par axe
              </h3>
              <RadarChartWrapper
                data={categoryAverages}
                name="Moyenne Catégorie"
                height={280}
                fillOpacity={0.25}
              />
            </div>
          </div>

          {/* Trust Markers Section - Takes 5 columns on large screens */}
          <div className="lg:col-span-5 order-1 lg:order-2">
            <div className="bg-white/[0.02] rounded-xl p-4 border border-white/5 h-full">
              <div className="flex items-center gap-2 mb-4">
                <div className="p-1.5 rounded-lg bg-emerald-500/10">
                  <ShieldCheck size={16} className="text-emerald-400" />
                </div>
                <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
                  Marqueurs de confiance clés
                </h3>
              </div>
              <p className="text-xs text-gray-500 mb-4 leading-relaxed">
                Points de parité de la catégorie et leur présence sur les produits analysés.
              </p>
              <TopTrustMarkers products={products} pointsOfParity={pointsOfParity} />
            </div>
          </div>

        </div>
      </div>
    </Card>
  );
}
