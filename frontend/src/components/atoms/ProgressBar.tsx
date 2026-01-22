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
  default: 'from-blue-500 to-blue-400',
  success: 'from-green-500 to-green-400',
  warning: 'from-yellow-500 to-yellow-400',
  error: 'from-red-500 to-red-400',
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
      <div className="h-2 bg-white/10 rounded-full overflow-hidden">
        <div
          className={cn('h-full bg-gradient-to-r rounded-full transition-all duration-300', variants[variant])}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <div className="text-xs text-gray-400 text-right">{Math.round(percentage)}%</div>
      )}
    </div>
  );
}
