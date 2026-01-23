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
    <Card>
      <h3 className="text-xl font-bold text-white mb-6">Nouvelle Analyse</h3>

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Catégorie de Produit"
          placeholder="ex: lait d'avoine, muesli bio, café moulu"
          value={category}
          onChange={setCategory}
          disabled={loading}
        />

        <div className="grid grid-cols-2 gap-4">
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
          <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-300 text-sm">
            {error}
          </div>
        )}

        <Button type="submit" loading={loading} className="w-full" size="lg">
          <Play size={18} />
          Lancer l'Analyse
        </Button>
      </form>
    </Card>
  );
}
