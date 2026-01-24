import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  hoverEffect?: boolean;
}

export const GlassCard: React.FC<GlassCardProps> = ({ 
  children, 
  className,
  hoverEffect = false
}) => {
  return (
    <motion.div
      className={cn(
        "relative overflow-hidden rounded-2xl border border-white/40 bg-white/20 shadow-xl backdrop-blur-md",
        "transition-all duration-300",
        className
      )}
      whileHover={hoverEffect ? { 
        scale: 1.02, 
        backgroundColor: "rgba(255, 255, 255, 0.3)",
        borderColor: "rgba(255, 255, 255, 0.6)",
        boxShadow: "0 20px 40px rgba(0, 0, 0, 0.1)"
      } : undefined}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-white/40 to-transparent opacity-50" />
      <div className="relative z-10 p-6">
        {children}
      </div>
    </motion.div>
  );
};
