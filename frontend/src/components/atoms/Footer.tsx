import React from 'react';
import { Calendar } from 'lucide-react';

interface FooterProps {
  variant?: 'light' | 'dark';
}

export const Footer: React.FC<FooterProps> = ({ variant = 'light' }) => {
  const textColor = variant === 'light' ? 'text-black/40' : 'text-white/40';
  const hoverColor = variant === 'light' ? 'hover:text-black/70' : 'hover:text-white/70';
  const brandColor = variant === 'light' ? 'text-black/60' : 'text-white/60';
  const linkBg = variant === 'light' 
    ? 'bg-black/5 hover:bg-black/10 border-black/10' 
    : 'bg-white/5 hover:bg-white/10 border-white/10';

  return (
    <footer className={`w-full py-6 px-4 ${textColor}`}>
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-sm font-medium">
          <span className={brandColor}>Powered by</span>
          <span className={`font-bold ${variant === 'light' ? 'text-black/70' : 'text-white/70'}`}>
            Iceberg AI
          </span>
        </div>
        
        <a 
          href="https://cal.com/adriel-aiach/30min"
          target="_blank"
          rel="noopener noreferrer"
          className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium border transition-all duration-200 ${linkBg} ${hoverColor}`}
        >
          <Calendar size={16} />
          <span>Réserver une démo</span>
        </a>
      </div>
    </footer>
  );
};
