import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ExternalLink, Home } from 'lucide-react';
import { useJobStatus } from '../hooks/useJobStatus';
import { Spinner, Button, Card, Footer } from '../components/atoms';
import { JobProgress } from '../components/organisms';
import { EmailModal } from '../landing_page/components/EmailModal';
import { api } from '../api/client';

/**
 * Job status page with real-time progress updates.
 */
export function JobStatus() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const { status, loading, error, isComplete, isFailed, refresh } = useJobStatus(jobId || null);
  const [showEmailModal, setShowEmailModal] = useState(false);

  // Check for DRAFT status to show modal
  useEffect(() => {
    if (status && status.state === 'DRAFT') {
        setShowEmailModal(true);
    } else {
        setShowEmailModal(false);
    }
  }, [status]);

  const handleEmailSuccess = async (email: string) => {
    if (!jobId) return;
    
    // Close modal immediately after email validation success
    setShowEmailModal(false);
    
    try {
        await api.scraper.start(jobId, email);
        // Refresh status to update from DRAFT to PENDING
        refresh();
    } catch (err) {
        console.error("Failed to start job after email:", err);
        // Optionally show an error toast here
    }
  };

  // No job ID
  if (!jobId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="text-center py-8 max-w-md bg-white/50 border-white/60">
          <div className="text-red-500 text-xl mb-4 font-bold">Aucun ID de tâche fourni</div>
          <Link to="/categories">
            <Button>
              <Home size={16} />
              Aller aux Catégories
            </Button>
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
  if (error && !status) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="text-center py-8 max-w-md bg-white/50 border-white/60">
          <div className="text-red-500 text-xl mb-2 font-bold">Échec du chargement du statut</div>
          <div className="text-gray-500 text-sm mb-6">{error}</div>
          <div className="flex gap-4 justify-center">
            <Button onClick={() => window.location.reload()}>Réessayer</Button>
            <Link to="/categories">
              <Button variant="secondary">
                <Home size={16} />
                Catégories
              </Button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  const handleViewResults = () => {
    if (status?.result?.category_slug && status?.result?.run_id) {
      navigate(`/category/${status.result.category_slug}_${status.result.run_id}`);
    } else if (status?.result?.run_id) {
      // Try to find the category from the run_id
      navigate('/categories');
    }
  };

  return (
    <div className="min-h-screen p-8 md:p-12 font-sans relative">
      <div className="max-w-2xl mx-auto space-y-8">
        {/* Header */}
        <header className="space-y-2">
          <h1 className="text-3xl font-bold text-gray-900">Analyse en cours</h1>
          <p className="text-gray-500 text-sm">Veuillez patienter pendant que notre IA analyse la catégorie. (Temps total estimé: 8 minutes)</p>
        </header>

        {/* Progress Card */}
        {status && <JobProgress job={status} />}

        {/* Actions */}
        <div className="flex gap-4">
          {isComplete && status?.result && (
            <Button onClick={handleViewResults} size="lg" className="flex-1 shadow-lg shadow-blue-500/20">
              <ExternalLink size={18} />
              Voir les Résultats
            </Button>
          )}

          {isFailed && (
            <Link to="/categories" className="flex-1">
              <Button variant="secondary" size="lg" className="w-full">
                Nouvelle Analyse
              </Button>
            </Link>
          )}

          {!isComplete && !isFailed && (
            <div className="text-sm text-gray-500 text-center flex-1 bg-white/30 p-3 rounded-xl border border-white/40 backdrop-blur-sm">
              Cette page se met à jour automatiquement. Vous pouvez partir et revenir plus tard.
            </div>
          )}
        </div>
      </div>

      {/* Email Modal Overlay */}
      <EmailModal 
        isOpen={showEmailModal} 
        onClose={() => {}} 
        onSuccess={handleEmailSuccess}
        canClose={false}
      />

      {/* Footer */}
      <div className="absolute bottom-0 left-0 right-0">
        <Footer variant="light" />
      </div>
    </div>
  );
}
