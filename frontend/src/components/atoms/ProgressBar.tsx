import React from 'react';
import { cn } from '../../lib/utils';

type ProgressBarProps = {
  value: number;
  max?: number;
  className?: string;
  showLabel?: boolean;
  variant?: 'default' | 'success' | 'warning' | 'error';
};

const variants = {
  default: 'from-blue-400 to-blue-300',
  success: 'from-green-400 to-green-300',
  warning: 'from-yellow-400 to-yellow-300',
  error: 'from-red-400 to-red-300',
};

export function ProgressBar({
  value,
  max = 100,
  className,
  showLabel = false,
  variant = 'default',
}: ProgressBarProps) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));

  return (
    <div className={cn('space-y-1', className)}>
      <div className="h-2.5 bg-white/40 rounded-full overflow-hidden shadow-inner border border-white/20 backdrop-blur-sm">
        <div
          className={cn('h-full bg-gradient-to-r rounded-full transition-all duration-500 ease-out shadow-sm', variants[variant])}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <div className="text-xs text-gray-500 font-medium text-right">{Math.round(percentage)}%</div>
      )}
    </div>
  );
}
