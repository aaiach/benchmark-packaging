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
    <Card className="p-0 overflow-hidden border-white/60 shadow-glass-lg backdrop-blur-3xl bg-white/40">
      {/* Header Section */}
      <div className="px-6 py-6 border-b border-white/50 bg-gradient-to-r from-white/40 to-transparent">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-3">
              <div className="p-2 bg-blue-50 rounded-xl shadow-sm">
                <BarChart3 className="text-blue-600" size={24} />
              </div>
              Aperçu de la catégorie
            </h2>
            <p className="text-gray-500 text-sm mt-1 ml-14">
              Analyse de positionnement sur {products.length} produits
            </p>
          </div>

          {/* Quick Stats Pills */}
          <div className="flex flex-wrap gap-3">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/60 border border-white/60 rounded-xl shadow-sm backdrop-blur-md">
              <Package size={16} className="text-blue-500" />
              <span className="text-sm font-semibold text-gray-700">{products.length} produits</span>
            </div>
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/60 border border-white/60 rounded-xl shadow-sm backdrop-blur-md">
              <Target size={16} className="text-purple-500" />
              <span className="text-sm font-semibold text-gray-700">{axisCount} axes</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="p-6 bg-white/20">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8">
          
          {/* Radar Chart Section - Takes 7 columns on large screens */}
          <div className="lg:col-span-7 order-2 lg:order-1">
            <div className="bg-white/40 rounded-2xl p-6 border border-white/60 shadow-sm h-full backdrop-blur-md">
              <h3 className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-6">
                Positionnement moyen par axe
              </h3>
              <RadarChartWrapper
                data={categoryAverages}
                name="Moyenne Catégorie"
                height={320}
                fillOpacity={0.4}
                color="#6366f1"
              />
            </div>
          </div>

          {/* Trust Markers Section - Takes 5 columns on large screens */}
          <div className="lg:col-span-5 order-1 lg:order-2">
            <div className="bg-white/40 rounded-2xl p-6 border border-white/60 shadow-sm h-full backdrop-blur-md">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 rounded-xl bg-emerald-50 text-emerald-600 shadow-sm">
                  <ShieldCheck size={20} />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wide">
                    Marqueurs de confiance
                  </h3>
                </div>
              </div>
              <p className="text-xs text-gray-500 mb-6 leading-relaxed bg-white/40 p-3 rounded-lg border border-white/50">
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
