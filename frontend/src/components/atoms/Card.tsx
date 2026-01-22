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
        'bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-6 shadow-xl',
        className
      )}
    >
      {children}
    </div>
  );
}
