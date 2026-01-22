import React from 'react';
import { cn } from '../../lib/utils';

type SpinnerSize = 'sm' | 'md' | 'lg';

type SpinnerProps = {
  size?: SpinnerSize;
  className?: string;
};

const sizes: Record<SpinnerSize, string> = {
  sm: 'h-4 w-4',
  md: 'h-8 w-8',
  lg: 'h-12 w-12',
};

export function Spinner({ size = 'md', className }: SpinnerProps) {
  return (
    <div
      className={cn(
        'animate-spin rounded-full border-b-2 border-blue-400',
        sizes[size],
        className
      )}
    />
  );
}
