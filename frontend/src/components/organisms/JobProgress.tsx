import React from 'react';
import { CheckCircle, XCircle, Clock, Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';
import { Card, Badge, ProgressBar } from '../atoms';
import type { JobStatus } from '../../types';

type JobProgressProps = {
  job: JobStatus;
};

const stateConfig: Record<
  string,
  { color: string; bg: string; icon: React.ComponentType<{ className?: string; size?: number }>; label: string }
> = {
  PENDING: { color: 'text-slate-500', bg: 'bg-slate-100', icon: Clock, label: 'En attente' },
  STARTED: { color: 'text-blue-600', bg: 'bg-blue-100', icon: Loader2, label: 'Démarrage' },
  PROGRESS: { color: 'text-blue-600', bg: 'bg-blue-100', icon: Loader2, label: 'En cours' },
  SUCCESS: { color: 'text-emerald-600', bg: 'bg-emerald-100', icon: CheckCircle, label: 'Terminé' },
  FAILURE: { color: 'text-red-600', bg: 'bg-red-100', icon: XCircle, label: 'Échec' },
};

const pipelineSteps = [
  { num: 1, name: 'Découverte des Marques' },
  { num: 2, name: 'Détails Produits' },
  { num: 3, name: 'Sélection d\'Images' },
  { num: 4, name: 'Téléchargement Images' },
  { num: 5, name: 'Analyse Visuelle' },
  { num: 6, name: 'Génération Heatmap' },
  { num: 7, name: 'Analyse Concurrentielle' },
];

/**
 * Displays job progress with step-by-step breakdown.
 */
export function JobProgress({ job }: JobProgressProps) {
  const config = stateConfig[job.state] || stateConfig.PENDING;
  const Icon = config.icon;
  const currentStep = job.current_step || 0;
  const progress = job.progress || 0;

  return (
    <Card className="glass-panel border-white/60 bg-white/40 shadow-glass-lg backdrop-blur-2xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <div className={cn("p-3 rounded-xl shadow-sm", config.bg, config.color)}>
            <Icon
              size={24}
              className={cn(
                job.state === 'PROGRESS' || job.state === 'STARTED' ? 'animate-spin' : ''
              )}
            />
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900">{config.label}</h3>
            <p className="text-sm text-gray-500 font-medium">{job.status}</p>
          </div>
        </div>
        <Badge
          variant={
            job.state === 'SUCCESS'
              ? 'success'
              : job.state === 'FAILURE'
              ? 'error'
              : 'info'
          }
          className="shadow-sm"
        >
          {job.state}
        </Badge>
      </div>

      {/* Progress Bar */}
      <div className="mb-8 bg-white/30 p-4 rounded-xl border border-white/40 shadow-sm">
        <div className="flex justify-between text-sm text-gray-600 font-semibold mb-3">
          <span>Progression Globale</span>
          <span>{progress}%</span>
        </div>
        <ProgressBar
          value={progress}
          variant={job.state === 'FAILURE' ? 'error' : job.state === 'SUCCESS' ? 'success' : 'default'}
        />
      </div>

      {/* Steps */}
      <div className="space-y-2">
        {pipelineSteps.map((step) => {
          const isActive = step.num === currentStep;
          const isCompleted = step.num < currentStep || job.state === 'SUCCESS';
          const isFailed = job.state === 'FAILURE' && step.num === currentStep;

          return (
            <div
              key={step.num}
              className={cn(
                'flex items-center gap-4 p-3 rounded-xl transition-all duration-300',
                isActive 
                  ? 'bg-white/80 shadow-glass-md border border-white/60 translate-x-1' 
                  : 'hover:bg-white/20',
                isCompleted && 'opacity-60 grayscale-[0.5]'
              )}
            >
              <div
                className={cn(
                  'w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shadow-sm transition-colors',
                  isCompleted
                    ? 'bg-emerald-100 text-emerald-600'
                    : isFailed
                    ? 'bg-red-100 text-red-600'
                    : isActive
                    ? 'bg-blue-600 text-white shadow-blue-200'
                    : 'bg-gray-100 text-gray-400'
                )}
              >
                {isCompleted ? '✓' : step.num}
              </div>
              <span
                className={cn(
                  'text-sm transition-colors',
                  isActive ? 'text-gray-900 font-bold' : 'text-gray-500'
                )}
              >
                {step.name}
              </span>
              {isActive && (job.state === 'PROGRESS' || job.state === 'STARTED') && (
                <Loader2 size={16} className="animate-spin text-blue-600 ml-auto" />
              )}
            </div>
          );
        })}
      </div>

      {/* Error Message */}
      {job.state === 'FAILURE' && job.error && (
        <div className="mt-8 p-5 bg-red-50/80 border border-red-200 rounded-xl text-red-600 text-sm font-medium shadow-sm backdrop-blur-sm">
          {job.error}
        </div>
      )}

      {/* Success Result */}
      {job.state === 'SUCCESS' && job.result && (
        <div className="mt-8 p-5 bg-emerald-50/80 border border-emerald-200 rounded-xl shadow-sm backdrop-blur-sm">
          <p className="text-emerald-800 text-sm font-bold mb-1">Analyse Terminée avec succès !</p>
        </div>
      )}
    </Card>
  );
}
