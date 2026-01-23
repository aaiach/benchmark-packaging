import React from 'react';
import { cn } from '../../lib/utils';

type BadgeVariant = 'default' | 'success' | 'outline' | 'info' | 'warning' | 'error';

type BadgeProps = {
  children: React.ReactNode;
  className?: string;
  variant?: BadgeVariant;
};

const variants: Record<BadgeVariant, string> = {
  default: 'bg-white/40 text-gray-700 border-white/50 backdrop-blur-md',
  success: 'bg-green-100/50 text-green-700 border-green-200/50 backdrop-blur-md',
  outline: 'border-white/60 text-gray-600 bg-transparent',
  info: 'bg-blue-100/50 text-blue-700 border-blue-200/50 backdrop-blur-md',
  warning: 'bg-yellow-100/50 text-yellow-700 border-yellow-200/50 backdrop-blur-md',
  error: 'bg-red-100/50 text-red-700 border-red-200/50 backdrop-blur-md',
};

export function Badge({ children, className, variant = 'default' }: BadgeProps) {
  return (
    <span
      className={cn(
        'px-3 py-1 rounded-full text-xs font-semibold border inline-flex items-center gap-1.5 shadow-sm',
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
