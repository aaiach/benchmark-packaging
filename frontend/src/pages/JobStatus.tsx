import React from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, ExternalLink, Home } from 'lucide-react';
import { useJobStatus } from '../hooks/useJobStatus';
import { Spinner, Button, Card } from '../components/atoms';
import { JobProgress } from '../components/organisms';

/**
 * Job status page with real-time progress updates.
 */
export function JobStatus() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const { status, loading, error, isComplete, isFailed } = useJobStatus(jobId || null);

  // No job ID
  if (!jobId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="text-center py-8 max-w-md">
          <div className="text-red-400 text-xl mb-4">No Job ID Provided</div>
          <Link to="/categories">
            <Button>
              <Home size={16} />
              Go to Categories
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
          <div className="text-white text-lg">Loading job status...</div>
        </div>
      </div>
    );
  }

  // Error state
  if (error && !status) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="text-center py-8 max-w-md">
          <div className="text-red-400 text-xl mb-2">Failed to Load Job Status</div>
          <div className="text-gray-400 text-sm mb-4">{error}</div>
          <div className="flex gap-4 justify-center">
            <Button onClick={() => window.location.reload()}>Retry</Button>
            <Link to="/categories">
              <Button variant="secondary">
                <Home size={16} />
                Categories
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
    <div className="min-h-screen p-8 md:p-12 font-sans">
      <div className="max-w-2xl mx-auto space-y-8">
        {/* Back Navigation */}
        <Link
          to="/categories"
          className="inline-flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
        >
          <ArrowLeft size={16} />
          All Categories
        </Link>

        {/* Header */}
        <header className="space-y-2">
          <h1 className="text-3xl font-bold text-white">Job Progress</h1>
          <p className="text-gray-400 text-sm font-mono">{jobId}</p>
        </header>

        {/* Progress Card */}
        {status && <JobProgress job={status} />}

        {/* Actions */}
        <div className="flex gap-4">
          {isComplete && status?.result && (
            <Button onClick={handleViewResults} size="lg" className="flex-1">
              <ExternalLink size={18} />
              View Analysis Results
            </Button>
          )}

          {isFailed && (
            <Link to="/categories" className="flex-1">
              <Button variant="secondary" size="lg" className="w-full">
                Start New Analysis
              </Button>
            </Link>
          )}

          {!isComplete && !isFailed && (
            <div className="text-sm text-gray-500 text-center flex-1">
              This page updates automatically. You can leave and come back later.
            </div>
          )}
        </div>

        {/* Job ID for reference */}
        <Card className="bg-white/5">
          <div className="text-xs text-gray-500 mb-1">Job ID (for reference)</div>
          <code className="text-sm text-gray-300 font-mono break-all">{jobId}</code>
        </Card>
      </div>
    </div>
  );
}
