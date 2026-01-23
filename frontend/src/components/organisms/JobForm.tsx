import React, { useState } from 'react';
import { Play } from 'lucide-react';
import { Card, Button, Input, Select } from '../atoms';
import { api } from '../../api/client';

type JobFormProps = {
  onJobStarted: (jobId: string) => void;
};

const countryOptions = [
  { value: 'France', label: 'France' },
  { value: 'Germany', label: 'Allemagne' },
  { value: 'UK', label: 'Royaume-Uni' },
  { value: 'USA', label: 'États-Unis' },
  { value: 'Spain', label: 'Espagne' },
  { value: 'Italy', label: 'Italie' },
  { value: 'Europe', label: 'Europe' },
];

const stepOptions = [
  { value: '1-7', label: 'Pipeline Complet (1-7)' },
  { value: '1-4', label: 'Découverte + Scraping (1-4)' },
  { value: '5-7', label: 'Analyse Uniquement (5-7)' },
  { value: '1-2', label: 'Découverte Uniquement (1-2)' },
];

/**
 * Form for submitting new scraper jobs.
 */
export function JobForm({ onJobStarted }: JobFormProps) {
  const [category, setCategory] = useState('');
  const [country, setCountry] = useState('France');
  const [count, setCount] = useState('30');
  const [steps, setSteps] = useState('1-7');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!category.trim()) {
      setError('La catégorie est requise');
      return;
    }

    const countNum = parseInt(count, 10);
    if (isNaN(countNum) || countNum < 1 || countNum > 100) {
      setError('Le nombre doit être entre 1 et 100');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.scraper.run({
        category: category.trim(),
        country,
        count: countNum,
        steps,
      });

      onJobStarted(response.job_id);
    } catch (err: any) {
      setError(err.message || 'Échec du lancement de la tâche');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="glass-panel border-white/60 bg-white/40 shadow-glass-lg backdrop-blur-2xl">
      <div className="flex items-center gap-3 mb-8">
        <div className="p-2.5 bg-blue-500/10 rounded-xl text-blue-600 shadow-sm">
          <Play size={20} fill="currentColor" className="opacity-20" />
        </div>
        <h3 className="text-xl font-bold text-gray-900">Nouvelle Analyse</h3>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Input
          label="Catégorie de Produit"
          placeholder="ex: lait d'avoine, muesli bio, café moulu"
          value={category}
          onChange={setCategory}
          disabled={loading}
          className="bg-white/40"
        />

        <div className="grid grid-cols-2 gap-6">
          <Select
            label="Pays"
            value={country}
            onChange={setCountry}
            options={countryOptions}
            disabled={loading}
          />

          <Input
            label="Nombre de Produits"
            type="number"
            value={count}
            onChange={setCount}
            min={1}
            max={100}
            disabled={loading}
          />
        </div>

        <Select
          label="Étapes du Pipeline"
          value={steps}
          onChange={setSteps}
          options={stepOptions}
          disabled={loading}
        />

        {error && (
          <div className="p-4 bg-red-50/80 border border-red-200 rounded-xl text-red-600 text-sm font-medium shadow-sm backdrop-blur-sm">
            {error}
          </div>
        )}

        <Button 
          type="submit" 
          loading={loading} 
          className="w-full bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-500/20 border-transparent h-12 text-base" 
          size="lg"
        >
          {loading ? 'Analyse en cours...' : "Lancer l'Analyse"}
          {!loading && <Play size={18} className="ml-2" />}
        </Button>
      </form>
    </Card>
  );
}
