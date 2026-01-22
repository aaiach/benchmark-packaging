import React from 'react';
import { cn } from '../../lib/utils';

type InputProps = {
  label?: string;
  placeholder?: string;
  value: string;
  onChange: (value: string) => void;
  className?: string;
  type?: 'text' | 'number' | 'email';
  disabled?: boolean;
  error?: string;
  min?: number;
  max?: number;
};

export function Input({
  label,
  placeholder,
  value,
  onChange,
  className,
  type = 'text',
  disabled = false,
  error,
  min,
  max,
}: InputProps) {
  return (
    <div className={cn('space-y-1', className)}>
      {label && (
        <label className="block text-sm font-medium text-gray-300">{label}</label>
      )}
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        min={min}
        max={max}
        className={cn(
          'w-full px-4 py-2 bg-white/5 border rounded-lg text-white placeholder-gray-500',
          'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          error ? 'border-red-500' : 'border-white/20'
        )}
      />
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  );
}
