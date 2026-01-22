import React, { useState } from 'react';
import { Play } from 'lucide-react';
import { Card, Button, Input, Select } from '../atoms';
import { api } from '../../api/client';

type JobFormProps = {
  onJobStarted: (jobId: string) => void;
};

const countryOptions = [
  { value: 'France', label: 'France' },
  { value: 'Germany', label: 'Germany' },
  { value: 'UK', label: 'United Kingdom' },
  { value: 'USA', label: 'United States' },
  { value: 'Spain', label: 'Spain' },
  { value: 'Italy', label: 'Italy' },
];

const stepOptions = [
  { value: '1-7', label: 'Full Pipeline (1-7)' },
  { value: '1-4', label: 'Discovery + Scraping (1-4)' },
  { value: '5-7', label: 'Analysis Only (5-7)' },
  { value: '1-2', label: 'Discovery Only (1-2)' },
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
      setError('Category is required');
      return;
    }

    const countNum = parseInt(count, 10);
    if (isNaN(countNum) || countNum < 1 || countNum > 100) {
      setError('Count must be between 1 and 100');
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
      setError(err.message || 'Failed to start job');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <h3 className="text-xl font-bold text-white mb-6">New Analysis Job</h3>

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Product Category"
          placeholder="e.g., lait d'avoine, muesli bio, café moulu"
          value={category}
          onChange={setCategory}
          disabled={loading}
        />

        <div className="grid grid-cols-2 gap-4">
          <Select
            label="Country"
            value={country}
            onChange={setCountry}
            options={countryOptions}
            disabled={loading}
          />

          <Input
            label="Product Count"
            type="number"
            value={count}
            onChange={setCount}
            min={1}
            max={100}
            disabled={loading}
          />
        </div>

        <Select
          label="Pipeline Steps"
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
          Start Analysis
        </Button>
      </form>
    </Card>
  );
}
