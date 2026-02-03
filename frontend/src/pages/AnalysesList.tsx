import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Eye, Calendar, Star, ImageIcon, Plus } from 'lucide-react';
import { api, API_URL } from '../api/client';
import { Footer, Spinner, Card } from '../components/atoms';

type AnalysisSummary = {
  job_id: string;
  brand: string;
  product_name: string;
  image_url: string | null;
  hierarchy_clarity_score: number | null;
  analyzed_at: string | null;
};

/**
 * Helper to construct full image URL using API base URL
 */
function getImageUrl(path: string | undefined | null): string | undefined {
  if (!path) return undefined;
  if (path.startsWith('http')) return path;
  return `${API_URL}${path}`;
}

/**
 * Format date for display
 */
function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'Date inconnue';
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return dateStr;
  }
}

/**
 * Page listing all single image analyses.
 */
export function AnalysesList() {
  const [analyses, setAnalyses] = useState<AnalysisSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalyses = async () => {
      try {
        const response = await api.imageAnalysis.listAnalyses();
        setAnalyses(response.analyses || []);
        setLoading(false);
      } catch (err: any) {
        setError(err.message || 'Erreur lors du chargement des analyses');
        setLoading(false);
      }
    };

    fetchAnalyses();
  }, []);

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <Spinner size="lg" />
          <div className="text-gray-600 text-lg font-medium">Chargement des analyses...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col font-sans">
      <div className="flex-1 p-8 md:p-12">
        <div className="max-w-6xl mx-auto space-y-8">
          {/* Back link */}
          <Link 
            to="/" 
            className="inline-flex items-center gap-2 text-gray-500 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft size={16} />
            <span className="text-sm font-medium">Accueil</span>
          </Link>

          {/* Header */}
          <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100 text-blue-600 text-xs font-bold uppercase tracking-wider shadow-sm">
                <Eye size={12} />
                Analyses
              </div>
              <h1 className="text-3xl md:text-4xl font-bold text-gray-900">
                Images analysées
              </h1>
              <p className="text-gray-500">
                {analyses.length} analyse{analyses.length !== 1 ? 's' : ''} disponible{analyses.length !== 1 ? 's' : ''}
              </p>
            </div>

            <Link to="/analyze">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-semibold shadow-lg hover:shadow-blue-500/25 transition-all flex items-center gap-2"
              >
                <Plus size={18} />
                Nouvelle analyse
              </motion.button>
            </Link>
          </header>

          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700">
              {error}
            </div>
          )}

          {/* Empty state */}
          {analyses.length === 0 && !error && (
            <Card className="text-center py-16">
              <ImageIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-700 mb-2">Aucune analyse</h3>
              <p className="text-gray-500 mb-6">Commencez par analyser une image de packaging</p>
              <Link to="/analyze">
                <button className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors">
                  Analyser une image
                </button>
              </Link>
            </Card>
          )}

          {/* Analyses Grid */}
          {analyses.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {analyses.map((analysis, index) => (
                <motion.div
                  key={analysis.job_id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Link to={`/analysis/${analysis.job_id}`}>
                    <Card className="group hover:shadow-lg hover:border-blue-200 transition-all cursor-pointer overflow-hidden">
                      {/* Image */}
                      <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden mb-4 -mx-4 -mt-4">
                        {analysis.image_url ? (
                          <img
                            src={getImageUrl(analysis.image_url)}
                            alt={analysis.product_name}
                            className="w-full h-full object-contain p-4 group-hover:scale-105 transition-transform duration-300"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-gray-400">
                            <ImageIcon size={48} />
                          </div>
                        )}
                      </div>

                      {/* Info */}
                      <div className="space-y-2">
                        <h3 className="font-semibold text-gray-900 truncate group-hover:text-blue-600 transition-colors">
                          {analysis.brand}
                        </h3>
                        <p className="text-sm text-gray-500 truncate">
                          {analysis.product_name}
                        </p>

                        {/* Meta */}
                        <div className="flex items-center justify-between pt-2 border-t border-gray-100">
                          {analysis.hierarchy_clarity_score !== null && (
                            <div className="flex items-center gap-1 text-sm">
                              <Star size={14} className="text-yellow-500" />
                              <span className="font-medium">{analysis.hierarchy_clarity_score}/10</span>
                            </div>
                          )}
                          <div className="flex items-center gap-1 text-xs text-gray-400">
                            <Calendar size={12} />
                            <span>{formatDate(analysis.analyzed_at)}</span>
                          </div>
                        </div>
                      </div>
                    </Card>
                  </Link>
                </motion.div>
              ))}
            </div>
          )}

          {/* Actions */}
          {analyses.length >= 2 && (
            <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-2xl border border-purple-100 p-6 text-center">
              <h3 className="font-semibold text-gray-900 mb-2">Prêt pour le rebranding ?</h3>
              <p className="text-gray-600 text-sm mb-4">
                Vous avez {analyses.length} analyses. Combinez-les pour créer un nouveau packaging.
              </p>
              <Link to="/rebrand">
                <button className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl font-semibold hover:from-purple-700 hover:to-pink-700 transition-all">
                  Lancer un rebranding
                </button>
              </Link>
            </div>
          )}
        </div>
      </div>

      <Footer variant="light" />
    </div>
  );
}
