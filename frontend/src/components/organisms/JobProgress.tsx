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
  { color: string; icon: React.ComponentType<{ className?: string; size?: number }>; label: string }
> = {
  PENDING: { color: 'text-gray-400', icon: Clock, label: 'En attente' },
  STARTED: { color: 'text-blue-400', icon: Loader2, label: 'Démarrage' },
  PROGRESS: { color: 'text-blue-400', icon: Loader2, label: 'En cours' },
  SUCCESS: { color: 'text-green-400', icon: CheckCircle, label: 'Terminé' },
  FAILURE: { color: 'text-red-400', icon: XCircle, label: 'Échec' },
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
    <Card>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Icon
            size={24}
            className={cn(
              config.color,
              job.state === 'PROGRESS' || job.state === 'STARTED' ? 'animate-spin' : ''
            )}
          />
          <div>
            <h3 className="text-lg font-bold text-white">{config.label}</h3>
            <p className="text-sm text-gray-400">{job.status}</p>
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
        >
          {job.state}
        </Badge>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between text-sm text-gray-400 mb-2">
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
                'flex items-center gap-3 p-2 rounded-lg transition-colors',
                isActive && 'bg-blue-500/10',
                isCompleted && 'opacity-60'
              )}
            >
              <div
                className={cn(
                  'w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium',
                  isCompleted
                    ? 'bg-green-500/20 text-green-400'
                    : isFailed
                    ? 'bg-red-500/20 text-red-400'
                    : isActive
                    ? 'bg-blue-500/20 text-blue-400'
                    : 'bg-white/10 text-gray-500'
                )}
              >
                {isCompleted ? '✓' : step.num}
              </div>
              <span
                className={cn(
                  'text-sm',
                  isActive ? 'text-white font-medium' : 'text-gray-400'
                )}
              >
                {step.name}
              </span>
              {isActive && (job.state === 'PROGRESS' || job.state === 'STARTED') && (
                <Loader2 size={14} className="animate-spin text-blue-400 ml-auto" />
              )}
            </div>
          );
        })}
      </div>

      {/* Error Message */}
      {job.state === 'FAILURE' && job.error && (
        <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-300 text-sm">
          {job.error}
        </div>
      )}

      {/* Success Result */}
      {job.state === 'SUCCESS' && job.result && (
        <div className="mt-4 p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
          <p className="text-green-300 text-sm font-medium mb-1">Analyse Terminée !</p>
          <p className="text-gray-400 text-xs">
            ID d'exécution : {job.result.run_id}
          </p>
        </div>
      )}
    </Card>
  );
}
