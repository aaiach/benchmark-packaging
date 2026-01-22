import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FolderOpen, Plus, RefreshCw } from 'lucide-react';
import { useCategories } from '../hooks/useCategories';
import { Spinner, Button, Card } from '../components/atoms';
import { CategoryCard, JobForm } from '../components/organisms';

/**
 * Categories list page with new job form.
 */
export function Categories() {
  const navigate = useNavigate();
  const { categories, loading, error, refetch } = useCategories();

  const handleJobStarted = (jobId: string) => {
    navigate(`/jobs/${jobId}`);
  };

  return (
    <div className="min-h-screen p-8 md:p-12 font-sans">
      <div className="max-w-7xl mx-auto space-y-12">
        {/* Header */}
        <header className="space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-300 text-xs font-medium uppercase tracking-wider">
            Competitive Intelligence Platform
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-white">Category Analysis</h1>
          <p className="text-lg text-gray-400 max-w-2xl">
            Explore existing competitive analyses or start a new one. Each analysis provides
            deep insights into product positioning, visual design, and market opportunities.
          </p>
        </header>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* New Job Form */}
          <div className="lg:col-span-1">
            <JobForm onJobStarted={handleJobStarted} />
          </div>

          {/* Categories List */}
          <div className="lg:col-span-2 space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <FolderOpen className="text-blue-400" size={24} />
                <h2 className="text-2xl font-bold">Existing Analyses</h2>
              </div>
              <Button variant="ghost" onClick={refetch} disabled={loading}>
                <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                Refresh
              </Button>
            </div>

            {loading && (
              <div className="flex items-center justify-center py-12">
                <Spinner size="lg" />
              </div>
            )}

            {error && (
              <Card className="text-center py-8">
                <div className="text-red-400 mb-2">Failed to load categories</div>
                <div className="text-gray-500 text-sm mb-4">{error}</div>
                <Button onClick={refetch}>Retry</Button>
              </Card>
            )}

            {!loading && !error && categories.length === 0 && (
              <Card className="text-center py-12">
                <FolderOpen size={48} className="mx-auto mb-4 text-gray-600" />
                <div className="text-gray-400 mb-2">No analyses yet</div>
                <div className="text-gray-500 text-sm">
                  Start your first analysis using the form on the left.
                </div>
              </Card>
            )}

            {!loading && !error && categories.length > 0 && (
              <div className="grid md:grid-cols-2 gap-4">
                {categories.map((category) => (
                  <CategoryCard key={category.id} category={category} />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
