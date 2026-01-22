import React from 'react';
import type { LucideIcon } from 'lucide-react';

type SectionTitleProps = {
  children: React.ReactNode;
  icon?: LucideIcon;
};

export function SectionTitle({ children, icon: Icon }: SectionTitleProps) {
  return (
    <h3 className="flex items-center gap-2 text-sm uppercase tracking-wider text-gray-400 mb-4 font-medium">
      {Icon && <Icon size={16} className="text-blue-400" />}
      {children}
    </h3>
  );
}
