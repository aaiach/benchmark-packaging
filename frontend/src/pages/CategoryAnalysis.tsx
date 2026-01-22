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
          <div className="text-white text-lg">Loading competitive analysis...</div>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4 max-w-md">
          <div className="text-red-400 text-xl font-bold">Error Loading Data</div>
          <div className="text-gray-400">{error || 'No data available'}</div>
          <div className="flex gap-4 justify-center">
            <Button onClick={refetch} variant="primary">
              Retry
            </Button>
            <Link to="/categories">
              <Button variant="secondary">
                <Home size={16} />
                All Categories
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
    <div className="min-h-screen p-8 md:p-12 font-sans selection:bg-pink-500/30">
      <div className="max-w-7xl mx-auto space-y-12">
        {/* Back Navigation */}
        <Link
          to="/categories"
          className="inline-flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
        >
          <ArrowLeft size={16} />
          All Categories
        </Link>

        {/* Header */}
        <header className="space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-300 text-xs font-medium uppercase tracking-wider">
            Competitive Benchmark 2026
          </div>
          <h1 className="text-5xl md:text-6xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/50 capitalize">
            {overview.name}
          </h1>
          <p className="text-lg text-gray-400 max-w-3xl leading-relaxed">
            {overview.summary}
          </p>
        </header>

        {/* Global Analysis */}
        <section>
          <CategoryLandscape products={products} axisDescriptions={axisDescriptions} />
        </section>

        {/* Strategic Insights */}
        {overview.strategic_insights.length > 0 && (
          <section>
            <div className="flex items-center gap-3 mb-6">
              <Lightbulb className="text-yellow-400" size={24} />
              <h2 className="text-2xl font-bold">Strategic Insights</h2>
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              {overview.strategic_insights.map((insight, idx) => (
                <InsightCard key={idx} insight={insight} />
              ))}
            </div>
          </section>
        )}

        {/* Product Grid */}
        <section>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold">Brand Portfolio ({products.length})</h2>
            <div className="text-sm text-gray-500">Click card for deep dive</div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
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
