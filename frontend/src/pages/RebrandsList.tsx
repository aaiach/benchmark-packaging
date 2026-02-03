import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Layers, Calendar, ImageIcon, Plus, CheckCircle, XCircle, ArrowRight } from 'lucide-react';
import { api, API_URL } from '../api/client';
import { Footer, Spinner, Card } from '../components/atoms';

type RebrandSummary = {
  job_id: string;
  status: string;
  created_at: string | null;
  completed_at: string | null;
  brand_identity: string;
  source_image_url: string | null;
  inspiration_image_url: string | null;
  generated_image_url: string | null;
  steps_completed: number;
  total_steps: number;
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
 * Status badge component
 */
function StatusBadge({ status, stepsCompleted, totalSteps }: { status: string; stepsCompleted: number; totalSteps: number }) {
  const isComplete = status === 'complete' || stepsCompleted === totalSteps;
  const isError = status === 'error';

  if (isComplete) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-green-100 text-green-700 text-xs font-medium">
        <CheckCircle size={12} />
        Terminé
      </span>
    );
  }

  if (isError) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-red-100 text-red-700 text-xs font-medium">
        <XCircle size={12} />
        Erreur
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-yellow-100 text-yellow-700 text-xs font-medium">
      {stepsCompleted}/{totalSteps} étapes
    </span>
  );
}

/**
 * Page listing all rebrand jobs.
 */
export function RebrandsList() {
  const [rebrands, setRebrands] = useState<RebrandSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRebrands = async () => {
      try {
        const response = await api.rebrand.list();
        setRebrands(response.jobs || []);
        setLoading(false);
      } catch (err: any) {
        setError(err.message || 'Erreur lors du chargement des rebrands');
        setLoading(false);
      }
    };

    fetchRebrands();
  }, []);

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <Spinner size="lg" />
          <div className="text-gray-600 text-lg font-medium">Chargement des rebrands...</div>
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
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-100 text-purple-600 text-xs font-bold uppercase tracking-wider shadow-sm">
                <Layers size={12} />
                Rebrands
              </div>
              <h1 className="text-3xl md:text-4xl font-bold text-gray-900">
                Historique des rebrands
              </h1>
              <p className="text-gray-500">
                {rebrands.length} rebrand{rebrands.length !== 1 ? 's' : ''} effectué{rebrands.length !== 1 ? 's' : ''}
              </p>
            </div>

            <Link to="/rebrand">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl font-semibold shadow-lg hover:shadow-purple-500/25 transition-all flex items-center gap-2"
              >
                <Plus size={18} />
                Nouveau rebrand
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
          {rebrands.length === 0 && !error && (
            <Card className="text-center py-16">
              <Layers className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-700 mb-2">Aucun rebrand</h3>
              <p className="text-gray-500 mb-6">Commencez par créer votre premier rebrand de packaging</p>
              <Link to="/rebrand">
                <button className="px-6 py-3 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors">
                  Créer un rebrand
                </button>
              </Link>
            </Card>
          )}

          {/* Rebrands List */}
          {rebrands.length > 0 && (
            <div className="space-y-4">
              {rebrands.map((rebrand, index) => (
                <motion.div
                  key={rebrand.job_id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Link to={`/rebrand/result/${rebrand.job_id}`}>
                    <Card className="group hover:shadow-lg hover:border-purple-200 transition-all cursor-pointer">
                      <div className="flex flex-col md:flex-row gap-4">
                        {/* Images preview */}
                        <div className="flex gap-2 flex-shrink-0">
                          {/* Source */}
                          <div className="w-20 h-20 bg-gray-100 rounded-lg overflow-hidden">
                            {rebrand.source_image_url ? (
                              <img
                                src={getImageUrl(rebrand.source_image_url)}
                                alt="Source"
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center text-gray-400">
                                <ImageIcon size={24} />
                              </div>
                            )}
                          </div>

                          {/* Arrow */}
                          <div className="flex items-center text-gray-300">
                            <ArrowRight size={16} />
                          </div>

                          {/* Inspiration */}
                          <div className="w-20 h-20 bg-gray-100 rounded-lg overflow-hidden">
                            {rebrand.inspiration_image_url ? (
                              <img
                                src={getImageUrl(rebrand.inspiration_image_url)}
                                alt="Inspiration"
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center text-gray-400">
                                <ImageIcon size={24} />
                              </div>
                            )}
                          </div>

                          {/* Arrow */}
                          <div className="flex items-center text-gray-300">
                            <ArrowRight size={16} />
                          </div>

                          {/* Generated */}
                          <div className="w-20 h-20 bg-gradient-to-br from-purple-100 to-pink-100 rounded-lg overflow-hidden border-2 border-purple-200">
                            {rebrand.generated_image_url ? (
                              <img
                                src={getImageUrl(rebrand.generated_image_url)}
                                alt="Résultat"
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center text-purple-400">
                                <Layers size={24} />
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Info */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-4">
                            <div className="space-y-1 min-w-0">
                              <h3 className="font-semibold text-gray-900 truncate group-hover:text-purple-600 transition-colors">
                                Rebrand #{rebrand.job_id.slice(0, 8)}
                              </h3>
                              <p className="text-sm text-gray-500 line-clamp-2">
                                {rebrand.brand_identity || 'Pas de description'}
                              </p>
                            </div>
                            <StatusBadge 
                              status={rebrand.status} 
                              stepsCompleted={rebrand.steps_completed} 
                              totalSteps={rebrand.total_steps} 
                            />
                          </div>

                          {/* Meta */}
                          <div className="flex items-center gap-4 mt-3 text-xs text-gray-400">
                            <div className="flex items-center gap-1">
                              <Calendar size={12} />
                              <span>{formatDate(rebrand.created_at)}</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <Layers size={12} />
                              <span>{rebrand.steps_completed}/{rebrand.total_steps} étapes</span>
                            </div>
                          </div>
                        </div>

                        {/* View button */}
                        <div className="flex items-center">
                          <div className="px-4 py-2 bg-purple-50 text-purple-600 rounded-lg text-sm font-medium group-hover:bg-purple-100 transition-colors">
                            Voir
                          </div>
                        </div>
                      </div>
                    </Card>
                  </Link>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>

      <Footer variant="light" />
    </div>
  );
}
