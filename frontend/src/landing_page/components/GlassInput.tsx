import React from 'react';
import { cn } from '../../lib/utils';

interface GlassInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export const GlassInput: React.FC<GlassInputProps> = ({ 
  className, 
  label,
  ...props 
}) => {
  return (
    <div className="w-full">
      {label && (
        <label className="mb-2 block text-sm font-medium text-black/70 ml-1">
          {label}
        </label>
      )}
      <input
        className={cn(
          "w-full rounded-xl border border-white/40 bg-white/30 px-4 py-3 text-black placeholder-black/40 shadow-sm backdrop-blur-sm",
          "focus:border-black/20 focus:bg-white/50 focus:outline-none focus:ring-0",
          "transition-all duration-200",
          className
        )}
        {...props}
      />
    </div>
  );
};
