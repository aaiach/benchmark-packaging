import React from 'react';
import { cn } from '../../lib/utils';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

type ButtonProps = {
  children: React.ReactNode;
  className?: string;
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
  loading?: boolean;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
};

const variants: Record<ButtonVariant, string> = {
  primary: 'glass-button text-gray-900 font-semibold active:shadow-inner',
  secondary: 'bg-white/20 hover:bg-white/40 text-gray-800 border border-white/30 shadow-sm backdrop-blur-sm',
  ghost: 'bg-transparent hover:bg-white/30 text-gray-700 border-transparent shadow-none',
  danger: 'bg-red-50/50 hover:bg-red-100/60 text-red-600 border border-red-200/50',
};

const sizes: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-sm rounded-lg',
  md: 'px-6 py-2.5 text-sm rounded-xl',
  lg: 'px-8 py-3.5 text-base rounded-2xl',
};

export function Button({
  children,
  className,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  onClick,
  type = 'button',
}: ButtonProps) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={cn(
        'inline-flex items-center justify-center gap-2 transition-all duration-300',
        'disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none',
        variants[variant],
        sizes[size],
        className
      )}
    >
      {loading && (
        <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-400 border-t-gray-800" />
      )}
      {children}
    </button>
  );
}
