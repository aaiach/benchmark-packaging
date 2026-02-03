import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCw, XCircle } from 'lucide-react';
import { api } from '../api/client';
import { Spinner, Card, Footer } from '../components/atoms';
import { JobProgress } from '../components/organisms';
import type { JobStatus as JobStatusType } from '../types';

/**
 * Rebrand job progress page.
 * Shows job progress while processing, then redirects to result page when complete.
 */
export function RebrandProgress() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const [status, setStatus] = useState<JobStatusType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Poll for status and redirect when complete
  useEffect(() => {
    if (!jobId) return;

    let isMounted = true;
    let pollInterval: ReturnType<typeof setInterval>;

    const fetchStatus = async () => {
      try {
        const statusResponse = await api.rebrand.getStatus(jobId);
        
        if (!isMounted) return;

        setStatus(statusResponse);
        setLoading(false);

        // If completed successfully, redirect to result page
        if (statusResponse.state === 'SUCCESS') {
          clearInterval(pollInterval);
          // Use the job_id as the rebrand ID (they are the same)
          navigate(`/rebrand/result/${jobId}`, { replace: true });
        } else if (statusResponse.state === 'FAILURE') {
          clearInterval(pollInterval);
          setError(statusResponse.error || 'Le rebranding a échoué');
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || 'Erreur lors de la récupération du statut');
          setLoading(false);
        }
      }
    };

    // Initial fetch
    fetchStatus();

    // Poll every 3 seconds while in progress
    pollInterval = setInterval(fetchStatus, 3000);

    return () => {
      isMounted = false;
      clearInterval(pollInterval);
    };
  }, [jobId, navigate]);

  // No job ID
  if (!jobId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="text-center py-8 max-w-md bg-white/50 border-white/60">
          <div className="text-red-500 text-xl mb-4 font-bold">Aucun ID de tâche fourni</div>
          <Link to="/rebrand">
            <button className="px-6 py-3 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors">
              Nouveau rebranding
            </button>
          </Link>
        </Card>
      </div>
    );
  }

  // Loading initial status
  if (loading && !status) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <Spinner size="lg" />
          <div className="text-gray-600 text-lg font-medium">Chargement du statut...</div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Card className="text-center py-8 max-w-md bg-white/50 border-white/60">
          <XCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <div className="text-red-500 text-xl mb-2 font-bold">Erreur</div>
          <div className="text-gray-500 text-sm mb-6">{error}</div>
          <div className="flex gap-4 justify-center">
            <button 
              onClick={() => window.location.reload()}
              className="px-6 py-3 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-colors flex items-center gap-2"
            >
              <RefreshCw size={16} />
              Réessayer
            </button>
            <Link to="/rebrand">
              <button className="px-6 py-3 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors">
                Nouveau rebranding
              </button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  // Show progress
  return (
    <div className="min-h-screen flex flex-col font-sans">
      <div className="flex-1 p-8 md:p-12">
        <div className="max-w-2xl mx-auto space-y-8">
          {/* Back link */}
          <Link 
            to="/rebrand" 
            className="inline-flex items-center gap-2 text-gray-500 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft size={16} />
            <span className="text-sm font-medium">Nouveau rebranding</span>
          </Link>

          {/* Header */}
          <header className="space-y-2">
            <h1 className="text-3xl font-bold text-gray-900">Rebranding en cours</h1>
            <p className="text-gray-500 text-sm">
              Notre IA génère votre nouveau packaging. Cette opération peut prendre quelques minutes...
            </p>
          </header>

          {/* Progress Card */}
          {status && <JobProgress job={status} />}

          {/* Info */}
          <div className="text-sm text-gray-500 text-center bg-white/30 p-3 rounded-xl border border-white/40 backdrop-blur-sm">
            Cette page se met à jour automatiquement. Vous serez redirigé vers les résultats une fois le rebranding terminé.
          </div>
        </div>
      </div>
      <Footer variant="light" />
    </div>
  );
}
