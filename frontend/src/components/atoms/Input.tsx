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
    <div className={cn('space-y-1.5', className)}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 ml-1">{label}</label>
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
          'glass-input w-full px-4 py-2.5 text-gray-900 placeholder-gray-400',
          'disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-50/50',
          error ? 'border-red-300 ring-2 ring-red-100' : 'hover:border-white/60'
        )}
      />
      {error && <p className="text-xs text-red-500 ml-1">{error}</p>}
    </div>
  );
}
