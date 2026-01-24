import React from 'react';
import { cn } from '../../lib/utils';
import { motion } from 'framer-motion';

export const LandingTitle: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className }) => (
  <h1 className={cn("text-4xl font-light tracking-tight text-black sm:text-6xl mb-6", className)}>
    {children}
  </h1>
);

export const LandingSubtitle: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className }) => (
  <p className={cn("text-lg text-black/60 font-light leading-relaxed max-w-2xl mx-auto mb-12", className)}>
    {children}
  </p>
);
