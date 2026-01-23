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
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-50/80 border border-blue-100 text-blue-600 text-xs font-bold uppercase tracking-wider shadow-sm backdrop-blur-md">
            Plateforme d'Intelligence Concurrentielle
          </div>
          <h1 className="text-4xl md:text-6xl font-black text-gray-900 tracking-tight">Analyse par Catégorie</h1>
          <p className="text-xl text-gray-500 max-w-2xl leading-relaxed font-light">
            Explorez les analyses concurrentielles existantes ou lancez-en une nouvelle. 
            Chaque analyse fournit des insights approfondis sur le positionnement produit.
          </p>
        </header>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* New Job Form */}
          <div className="lg:col-span-1">
            <JobForm onJobStarted={handleJobStarted} />
          </div>

          {/* Categories List */}
          <div className="lg:col-span-2 space-y-6">
            <div className="flex items-center justify-between bg-white/30 p-4 rounded-2xl backdrop-blur-md border border-white/40">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-50 rounded-lg">
                  <FolderOpen className="text-blue-500" size={24} />
                </div>
                <h2 className="text-2xl font-bold text-gray-800">Analyses Existantes</h2>
              </div>
              <Button variant="ghost" onClick={refetch} disabled={loading} className="hover:bg-white/50">
                <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                Actualiser
              </Button>
            </div>

            {loading && (
              <div className="flex items-center justify-center py-12">
                <Spinner size="lg" />
              </div>
            )}

            {error && (
              <Card className="text-center py-8 border-red-100 bg-red-50/50">
                <div className="text-red-500 mb-2 font-medium">Échec du chargement des catégories</div>
                <div className="text-gray-500 text-sm mb-4">{error}</div>
                <Button onClick={refetch}>Réessayer</Button>
              </Card>
            )}

            {!loading && !error && categories.length === 0 && (
              <Card className="text-center py-16 border-dashed border-2 border-gray-200 bg-white/20">
                <FolderOpen size={48} className="mx-auto mb-4 text-gray-300" />
                <div className="text-gray-500 mb-2 font-medium">Aucune analyse pour le moment</div>
                <div className="text-gray-400 text-sm">
                  Lancez votre première analyse avec le formulaire à gauche.
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
