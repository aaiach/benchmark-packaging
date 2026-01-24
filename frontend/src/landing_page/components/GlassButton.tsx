import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';
import { Loader2 } from 'lucide-react';

interface GlassButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost';
  isLoading?: boolean;
  children?: React.ReactNode;
  className?: string;
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
  onClick?: React.MouseEventHandler<HTMLButtonElement>;
}

export const GlassButton: React.FC<GlassButtonProps> = ({ 
  children, 
  className, 
  variant = 'primary',
  isLoading,
  disabled,
  type,
  onClick,
}) => {
  const variants = {
    primary: "bg-black/80 text-white hover:bg-black border border-transparent shadow-lg",
    secondary: "bg-white/40 text-black border border-white/60 hover:bg-white/60 shadow-md",
    ghost: "bg-transparent text-black hover:bg-black/5"
  };

  return (
    <motion.button
      type={type}
      onClick={onClick}
      className={cn(
        "relative flex items-center justify-center rounded-xl px-6 py-3 font-medium transition-all duration-200",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        variants[variant],
        className
      )}
      whileHover={!disabled && !isLoading ? { scale: 1.02 } : undefined}
      whileTap={!disabled && !isLoading ? { scale: 0.98 } : undefined}
      disabled={disabled || isLoading}
    >
      {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
      {children}
    </motion.button>
  );
};
