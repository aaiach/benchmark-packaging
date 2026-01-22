import React from 'react';
import { cn } from '../../lib/utils';

type BadgeVariant = 'default' | 'success' | 'outline' | 'info' | 'warning' | 'error';

type BadgeProps = {
  children: React.ReactNode;
  className?: string;
  variant?: BadgeVariant;
};

const variants: Record<BadgeVariant, string> = {
  default: 'bg-white/10 text-white border-white/20',
  success: 'bg-green-500/20 text-green-300 border-green-500/30',
  outline: 'border-white/30 text-white/70',
  info: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  warning: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  error: 'bg-red-500/20 text-red-300 border-red-500/30',
};

export function Badge({ children, className, variant = 'default' }: BadgeProps) {
  return (
    <span
      className={cn(
        'px-2.5 py-0.5 rounded-full text-xs font-medium border inline-flex items-center gap-1',
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
