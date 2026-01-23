import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Lightbulb, ArrowLeft, Home } from 'lucide-react';
import { useCategoryData } from '../hooks/useCategoryData';
import { Spinner, Button } from '../components/atoms';
import {
  CategoryLandscape,
  InsightCard,
  ProductCard,
  ProductModal,
} from '../components/organisms';
import type { Product, PointOfDifference, PointOfParity } from '../types';

/**
 * Main category analysis page.
 * Shows competitive analysis, products grid, and insights.
 */
export function CategoryAnalysis() {
  const { categoryId } = useParams<{ categoryId: string }>();
  const { data, loading, error, refetch } = useCategoryData(categoryId || null);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <Spinner size="lg" />
          <div className="text-gray-600 text-lg font-medium">Chargement de l'analyse concurrentielle...</div>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4 max-w-md p-8 glass-card bg-white/50">
          <div className="text-red-500 text-xl font-bold">Erreur de Chargement</div>
          <div className="text-gray-600">{error || 'Aucune donnée disponible'}</div>
          <div className="flex gap-4 justify-center">
            <Button onClick={refetch} variant="primary">
              Réessayer
            </Button>
            <Link to="/categories">
              <Button variant="secondary">
                <Home size={16} />
                Toutes les Catégories
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const { overview, products } = data;

  // Build axis descriptions from points of difference
  const axisDescriptions: Record<string, string> = Object.fromEntries(
    overview.points_of_difference.map((pod) => [pod.axis_id, pod.axis_name])
  );

  return (
    <div className="min-h-screen p-8 md:p-12 font-sans selection:bg-blue-100 selection:text-blue-900">
      <div className="max-w-7xl mx-auto space-y-12">
        {/* Header */}
        <header className="space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-100 text-blue-600 text-xs font-bold uppercase tracking-wider shadow-sm">
            Benchmark Concurrentiel 2026
          </div>
          <h1 className="text-5xl md:text-7xl font-black text-gray-900 capitalize tracking-tight">
            {overview.name}
          </h1>
          <p className="text-xl text-gray-500 max-w-3xl leading-relaxed font-light">
            {overview.summary}
          </p>
        </header>

        {/* Global Analysis */}
        <section>
          <CategoryLandscape
            products={products}
            axisDescriptions={axisDescriptions}
            pointsOfParity={overview.points_of_parity}
          />
        </section>

        {/* Strategic Insights */}
        {overview.strategic_insights.length > 0 && (
          <section>
            <div className="flex items-center gap-3 mb-8">
              <div className="p-2 bg-yellow-50 rounded-xl shadow-sm">
                <Lightbulb className="text-yellow-500" size={24} />
              </div>
              <h2 className="text-2xl font-bold text-gray-900">Insights Stratégiques</h2>
            </div>
            <div className="grid md:grid-cols-2 gap-6">
              {overview.strategic_insights.map((insight, idx) => (
                <InsightCard key={idx} insight={insight} />
              ))}
            </div>
          </section>
        )}

        {/* Product Grid */}
        <section>
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl font-bold text-gray-900">Portfolio Marques <span className="text-gray-400 font-normal">({products.length})</span></h2>
            <div className="text-sm text-gray-500 font-medium bg-white/40 px-3 py-1 rounded-full border border-white/60">Cliquez pour approfondir</div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6">
            {products.map((product) => (
              <ProductCard
                key={product.id + product.name}
                product={product}
                onClick={() => setSelectedProduct(product)}
                pointsOfParity={overview.points_of_parity}
              />
            ))}
          </div>
        </section>
      </div>

      {/* Detail Modal */}
      {selectedProduct && (
        <ProductModal
          product={selectedProduct}
          onClose={() => setSelectedProduct(null)}
          pointsOfDifference={overview.points_of_difference}
          pointsOfParity={overview.points_of_parity}
          axisDescriptions={axisDescriptions}
        />
      )}
    </div>
  );
}
