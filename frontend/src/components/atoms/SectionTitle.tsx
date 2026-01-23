import React from 'react';
import type { LucideIcon } from 'lucide-react';

type SectionTitleProps = {
  children: React.ReactNode;
  icon?: LucideIcon;
};

export function SectionTitle({ children, icon: Icon }: SectionTitleProps) {
  return (
    <h3 className="flex items-center gap-2.5 text-sm uppercase tracking-widest text-gray-500 mb-6 font-semibold">
      {Icon && <Icon size={16} className="text-gray-800" />}
      {children}
    </h3>
  );
}
