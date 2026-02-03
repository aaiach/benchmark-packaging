import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Lightbulb, Home, Sparkles } from 'lucide-react';
import { useCategoryData } from '../hooks/useCategoryData';
import { api } from '../api/client';
import { Spinner, Button, Footer } from '../components/atoms';
import {
  CategoryLandscape,
  InsightCard,
  ProductCard,
  ProductModal,
  RebrandSessionModal,
  RebrandSessionResults,
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
  
  // Rebrand session state
  const [showRebrandModal, setShowRebrandModal] = useState(false);
  const [rebrandSession, setRebrandSession] = useState<any>(null);
  const [rebrandLoading, setRebrandLoading] = useState(false);
  const [rebrandPolling, setRebrandPolling] = useState(false);
  
  // Load existing rebrand session for this analysis
  const loadRebrandSession = useCallback(async () => {
    if (!categoryId) return;
    
    setRebrandLoading(true);
    try {
      const session = await api.rebrandSession.getForAnalysis(categoryId);
      setRebrandSession(session);
      
      // If session is not complete, start polling for real-time updates
      const isComplete = ['completed', 'partial', 'failed'].includes(session.status);
      if (!isComplete) {
        setRebrandPolling(true);
      } else {
        setRebrandPolling(false);
      }
    } catch (err: any) {
      // 404 means no session exists, which is fine
      if (err.status !== 404) {
        console.error('Failed to load rebrand session:', err);
      }
      setRebrandSession(null);
      setRebrandPolling(false);
    } finally {
      setRebrandLoading(false);
    }
  }, [categoryId]);
  
  // Load rebrand session on mount
  useEffect(() => {
    loadRebrandSession();
  }, [loadRebrandSession]);
  
  // Poll for rebrand session updates
  useEffect(() => {
    if (!rebrandPolling || !rebrandSession?.session_id) return;
    
    const interval = setInterval(async () => {
      try {
        const status = await api.rebrandSession.getStatus(rebrandSession.session_id);
        
        // Check if session is complete (completed, partial, or failed)
        const isComplete = ['completed', 'partial', 'failed'].includes(status.status);
        
        // Update session with new data from status endpoint
        setRebrandSession((prev: any) => ({
          ...prev,
          status: status.status,
          rebrands: status.rebrands || prev?.rebrands || [],
          progress: {
            total: status.total || prev?.progress?.total || 0,
            completed: status.completed || 0,
            failed: status.failed || 0,
            current_product: null,
          },
        }));
        
        if (isComplete) {
          setRebrandPolling(false);
        }
      } catch (err) {
        console.error('Failed to poll rebrand status:', err);
      }
    }, 3000);
    
    return () => clearInterval(interval);
  }, [rebrandPolling, rebrandSession?.session_id]);
  
  // Handle new session started
  const handleSessionStarted = useCallback((sessionId: string) => {
    setRebrandSession(null); // Clear previous session immediately
    setRebrandPolling(true);
    loadRebrandSession();
  }, [loadRebrandSession]);
  
  // Handle retry
  const handleRetryRebrand = useCallback(() => {
    setShowRebrandModal(true);
  }, []);

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
    <div className="min-h-screen p-4 sm:p-8 md:p-12 font-sans selection:bg-blue-100 selection:text-blue-900 overflow-x-hidden">
      <div className="max-w-7xl mx-auto space-y-8 md:space-y-12">
        {/* Header */}
        <header className="space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-100 text-blue-600 text-xs font-bold uppercase tracking-wider shadow-sm">
            Benchmark Concurrentiel 2026
          </div>
          <h1 className="text-3xl sm:text-5xl md:text-7xl font-black text-gray-900 capitalize tracking-tight">
            {overview.name}
          </h1>
          <p className="text-base sm:text-xl text-gray-500 max-w-3xl leading-relaxed font-light">
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
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
              {overview.strategic_insights.map((insight, idx) => (
                <InsightCard key={idx} insight={insight} />
              ))}
            </div>
          </section>
        )}

        {/* Rebrand CTA Banner */}
        {!rebrandSession && (
          <section className="relative overflow-hidden rounded-2xl sm:rounded-3xl bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 p-6 sm:p-8 md:p-12 text-white shadow-2xl isolate">
            <div className="relative z-10 max-w-2xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/20 backdrop-blur-md text-xs font-bold uppercase tracking-wider mb-6 border border-white/30 text-white/90 shadow-sm">
                <Sparkles size={12} />
                Nouveau
              </div>
              <h2 className="text-2xl sm:text-3xl md:text-5xl font-black mb-4 sm:mb-6 tracking-tight">
                Imaginez le futur de votre marque
              </h2>
              <p className="text-base sm:text-lg text-white/90 mb-6 sm:mb-8 leading-relaxed max-w-xl font-medium">
                Générez instantanément des concepts de rebranding uniques basés sur l'analyse approfondie de vos concurrents.
              </p>
              <Button 
                onClick={() => setShowRebrandModal(true)} 
                className="bg-white text-purple-600 hover:bg-purple-50 border-none px-5 py-3 sm:px-8 sm:py-4 h-auto text-sm sm:text-lg font-bold shadow-xl hover:shadow-2xl transition-all transform hover:-translate-y-1"
              >
                <Sparkles className="mr-2" />
                Lancer une session de Rebranding
              </Button>
            </div>
            
            {/* Decorative elements - hidden on mobile to prevent overflow */}
            <div className="hidden sm:block absolute top-0 right-0 -mr-20 -mt-20 w-96 h-96 bg-white/10 rounded-full blur-3xl mix-blend-overlay" />
            <div className="hidden sm:block absolute bottom-0 right-20 w-72 h-72 bg-purple-900/30 rounded-full blur-3xl mix-blend-overlay" />
          </section>
        )}

        {/* Product Grid */}
        <section>
          <div className="flex items-center justify-between mb-6 sm:mb-8">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Portfolio Marques <span className="text-gray-400 font-normal">({products.length})</span></h2>
            <div className="hidden sm:flex items-center gap-4">
              <div className="text-sm text-gray-500 font-medium bg-white/40 px-3 py-1 rounded-full border border-white/60">Cliquez pour approfondir</div>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 sm:gap-6">
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
        
        {/* Rebrand Session Results */}
        {rebrandSession && (
          <section className="mt-12 pt-12 border-t border-gray-200">
            <RebrandSessionResults
              session={rebrandSession}
              onRetry={handleRetryRebrand}
            />
          </section>
        )}

        {/* Footer */}
        <Footer variant="light" />
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
      
      {/* Rebrand Session Modal */}
      <RebrandSessionModal
        isOpen={showRebrandModal}
        onClose={() => setShowRebrandModal(false)}
        analysisId={categoryId || ''}
        category={overview.name}
        productCount={products.filter(p => p.image || p.image_url || p.local_image_path).length}
        onSessionStarted={handleSessionStarted}
      />
    </div>
  );
}
