import React from 'react';
import { cn } from '../../lib/utils';

type CardProps = {
  children: React.ReactNode;
  className?: string;
};

export function Card({ children, className }: CardProps) {
  return (
    <div
      className={cn(
        'glass-card p-6 transition-all duration-300 hover:shadow-glass-lg hover:bg-white/60',
        className
      )}
    >
      {children}
    </div>
  );
}
