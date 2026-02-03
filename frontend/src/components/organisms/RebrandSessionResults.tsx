import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  Loader2,
  Download,
  ChevronLeft,
  ChevronRight,
  Maximize2,
  Image as ImageIcon,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { Card, Button, Badge, ProgressBar } from '../atoms';
import { API_URL } from '../../api/client';
import { cn } from '../../lib/utils';

type RebrandEntry = {
  product_index: number;
  product_name: string;
  inspiration_image_path: string;
  inspiration_image_url?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped';
  generated_image_path?: string;
  generated_image_url?: string;
  error?: string;
};

type RebrandSessionResultsProps = {
  session: {
    session_id: string;
    source_image_url?: string;
    source_image_path: string;
    status: string;
    rebrands: RebrandEntry[];
    progress: {
      total: number;
      completed: number;
      failed: number;
      current_product?: string;
    };
  };
  onRetry?: () => void;
};

function getImageUrl(path: string | undefined): string | undefined {
  if (!path) return undefined;
  if (path.startsWith('http')) return path;
  return `${API_URL}${path}`;
}

export function RebrandSessionResults({ session, onRetry }: RebrandSessionResultsProps) {
  // Filter out rebrands that are effectively viewable or in progress
  const displayableRebrands = session.rebrands.filter(
    r => r.status === 'completed' || r.status === 'in_progress' || r.status === 'pending'
  );
  
  // Also keep track of failures for stats
  const failedCount = session.rebrands.filter(r => r.status === 'failed').length;
  
  const [selectedIndex, setSelectedIndex] = useState(0);
  const selectedRebrand = displayableRebrands[selectedIndex];
  
  // Ensure selection is valid if list changes
  React.useEffect(() => {
    if (selectedIndex >= displayableRebrands.length && displayableRebrands.length > 0) {
      setSelectedIndex(0);
    }
  }, [displayableRebrands.length, selectedIndex]);

  const sourceImageUrl = getImageUrl(session.source_image_url || session.source_image_path);
  const isSessionComplete = ['completed', 'partial', 'failed'].includes(session.status);
  const progressPercent = session.progress.total > 0
    ? Math.round(((session.progress.completed + session.progress.failed) / session.progress.total) * 100)
    : 0;

  const isAllFailed = isSessionComplete && displayableRebrands.length === 0;
  
  const nextSlide = () => {
    setSelectedIndex((prev) => (prev + 1) % displayableRebrands.length);
  };

  const prevSlide = () => {
    setSelectedIndex((prev) => (prev - 1 + displayableRebrands.length) % displayableRebrands.length);
  };

  if (isAllFailed) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center space-y-4 bg-red-50/50 rounded-3xl border border-red-100">
        <AlertCircle className="w-12 h-12 text-red-400" />
        <h3 className="text-xl font-bold text-gray-900">Génération échouée</h3>
        <p className="text-gray-600 max-w-md">
          Nous n'avons pas pu générer de variantes pour cette session. Cela peut être dû à une erreur temporaire ou aux images sources.
        </p>
        {onRetry && (
          <Button onClick={onRetry} variant="primary" className="mt-4">
            <RefreshCw size={16} className="mr-2" />
            Réessayer
          </Button>
        )}
      </div>
    );
  }

  if (displayableRebrands.length === 0 && !isSessionComplete) {
     return (
       <div className="flex flex-col items-center justify-center p-12 text-center space-y-4">
         <Loader2 className="w-12 h-12 text-purple-500 animate-spin" />
         <h3 className="text-xl font-semibold text-gray-900">Initialisation du Rebranding...</h3>
         <p className="text-gray-500">Préparation des variantes de design</p>
       </div>
     );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      {/* Header & Stats */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h2 className="text-3xl font-black text-gray-900 tracking-tight mb-2">
            Résultats du Rebranding
          </h2>
          <div className="flex items-center gap-3 text-sm">
             <Badge variant={isSessionComplete ? 'success' : 'warning'} className="gap-1.5 px-3 py-1">
               {isSessionComplete ? <Sparkles size={14} /> : <Loader2 size={14} className="animate-spin" />}
               {isSessionComplete ? 'Terminé' : 'En cours de génération...'}
             </Badge>
             <span className="text-gray-500 font-medium">
               {session.progress.completed} designs générés
               {failedCount > 0 && ` • ${failedCount} échecs`}
             </span>
          </div>
        </div>
        
        {/* Progress Bar (if active) */}
        {!isSessionComplete && (
          <div className="flex-1 max-w-md bg-white/50 p-4 rounded-xl border border-white/60 shadow-sm backdrop-blur-sm">
            <div className="flex justify-between text-xs font-semibold text-gray-600 mb-2">
              <span>Génération en cours...</span>
              <span>{progressPercent}%</span>
            </div>
            <ProgressBar value={progressPercent} className="h-2" />
            {session.progress.current_product && (
               <div className="mt-2 text-xs text-purple-600 truncate">
                 Design pour : {session.progress.current_product}
               </div>
            )}
          </div>
        )}
      </div>

      {/* Main Recipe View */}
      {selectedRebrand && (
        <div className="bg-white/30 backdrop-blur-md border border-white/60 rounded-3xl p-6 md:p-8 shadow-xl">
          <div className="flex flex-col lg:flex-row items-stretch lg:items-center gap-6 lg:gap-12 min-h-[400px]">
            
            {/* Left Column: Source (Input) */}
            <div className="w-full lg:w-1/4 flex flex-col items-center">
              <div className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-500"></span> Source
              </div>
              <div className="relative w-full aspect-square max-w-[200px] lg:max-w-none rounded-2xl bg-white border border-gray-200 shadow-sm overflow-hidden group hover:shadow-md transition-all duration-300">
                {sourceImageUrl ? (
                  <img 
                    src={sourceImageUrl} 
                    alt="Source" 
                    className="w-full h-full object-contain p-4 transition-transform duration-500 group-hover:scale-105" 
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-300">
                    <ImageIcon size={32} />
                  </div>
                )}
              </div>
            </div>

            {/* Middle Column: Result (Output) */}
            <div className="flex-1 flex flex-col items-center justify-center order-first lg:order-none relative">
              <div className="text-xs font-bold text-purple-600 uppercase tracking-wider mb-3 flex items-center gap-2">
                <Sparkles size={12} /> Résultat
              </div>
              
              <div className="relative w-full aspect-[4/3] rounded-3xl bg-white shadow-2xl overflow-hidden border-4 border-white/50 group">
                {selectedRebrand.status === 'completed' ? (
                  <>
                    <img 
                      src={getImageUrl(selectedRebrand.generated_image_url || selectedRebrand.generated_image_path)} 
                      alt="Rebrand Result"
                      className="w-full h-full object-contain p-4 lg:p-8"
                    />
                    
                    {/* Hover Actions */}
                    <div className="absolute inset-0 bg-black/40 backdrop-blur-[2px] opacity-0 group-hover:opacity-100 transition-all duration-300 flex items-center justify-center gap-4">
                      <a 
                        href={getImageUrl(selectedRebrand.generated_image_url || selectedRebrand.generated_image_path)}
                        download
                        className="p-4 bg-white rounded-full text-gray-900 hover:text-purple-600 hover:scale-110 transition-all shadow-xl"
                        title="Télécharger"
                      >
                        <Download size={24} />
                      </a>
                      <button 
                        className="p-4 bg-white rounded-full text-gray-900 hover:text-blue-600 hover:scale-110 transition-all shadow-xl"
                        onClick={() => window.open(getImageUrl(selectedRebrand.generated_image_url || selectedRebrand.generated_image_path), '_blank')}
                      >
                        <Maximize2 size={24} />
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-50/50">
                    {selectedRebrand.status === 'failed' ? (
                      <>
                        <AlertCircle size={48} className="text-red-200 mb-4" />
                        <p className="text-sm font-medium text-red-400">Génération échouée</p>
                      </>
                    ) : (
                      <>
                        <Loader2 size={48} className="animate-spin text-purple-200 mb-4" />
                        <p className="text-sm font-medium text-purple-400 animate-pulse">Génération...</p>
                      </>
                    )}
                  </div>
                )}

                {/* Navigation Arrows (Desktop) */}
                <button 
                  onClick={(e) => { e.stopPropagation(); prevSlide(); }}
                  className="absolute left-4 top-1/2 -translate-y-1/2 p-2 rounded-full bg-white/80 hover:bg-white text-gray-700 shadow-lg opacity-0 group-hover:opacity-100 transition-all hidden lg:block"
                >
                  <ChevronLeft size={24} />
                </button>
                <button 
                  onClick={(e) => { e.stopPropagation(); nextSlide(); }}
                  className="absolute right-4 top-1/2 -translate-y-1/2 p-2 rounded-full bg-white/80 hover:bg-white text-gray-700 shadow-lg opacity-0 group-hover:opacity-100 transition-all hidden lg:block"
                >
                  <ChevronRight size={24} />
                </button>
              </div>
            </div>

            {/* Right Column: Inspiration (Input) */}
            <div className="w-full lg:w-1/4 flex flex-col items-center">
              <div className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-purple-500"></span> Inspiration
              </div>
              <div className="relative w-full aspect-square max-w-[200px] lg:max-w-none rounded-2xl bg-white border border-gray-200 shadow-sm overflow-hidden group hover:shadow-md transition-all duration-300">
                <img 
                  src={getImageUrl(selectedRebrand.inspiration_image_url || selectedRebrand.inspiration_image_path)}
                  alt="Inspiration"
                  className="w-full h-full object-contain p-4 transition-transform duration-500 group-hover:scale-105"
                />
                <div className="absolute bottom-0 inset-x-0 p-3 bg-gradient-to-t from-black/60 to-transparent">
                  <p className="text-xs font-medium text-white text-center truncate">
                    {selectedRebrand.product_name}
                  </p>
                </div>
              </div>
            </div>

          </div>
        </div>
      )}

      {/* Discrete Bottom Navigation */}
      <div className="flex justify-center mt-8">
        <div className="flex items-center gap-4 bg-white/40 backdrop-blur-md px-6 py-3 rounded-full border border-white/60 shadow-sm">
          <button 
            onClick={prevSlide}
            className="p-2 hover:bg-white rounded-full text-gray-500 hover:text-gray-900 transition-colors"
          >
            <ChevronLeft size={20} />
          </button>
          
          <div className="flex gap-2 max-w-[200px] md:max-w-md overflow-x-auto hide-scrollbar px-2 py-2">
            {displayableRebrands.map((rebrand, idx) => (
              <button
                key={idx}
                onClick={() => setSelectedIndex(idx)}
                className={cn(
                  "relative w-12 h-12 rounded-lg overflow-hidden transition-all duration-300 border-2 flex-shrink-0",
                  idx === selectedIndex 
                    ? "border-purple-600 shadow-md scale-110 z-10" 
                    : "border-transparent opacity-60 hover:opacity-100 hover:border-purple-300"
                )}
                title={rebrand.product_name}
              >
                <img 
                  src={getImageUrl(rebrand.inspiration_image_url || rebrand.inspiration_image_path)}
                  alt={rebrand.product_name}
                  className="w-full h-full object-cover"
                />
              </button>
            ))}
          </div>

          <button 
            onClick={nextSlide}
            className="p-2 hover:bg-white rounded-full text-gray-500 hover:text-gray-900 transition-colors"
          >
            <ChevronRight size={20} />
          </button>
          
          <div className="h-4 w-px bg-gray-300 mx-2" />
          
          <span className="text-xs font-medium text-gray-500">
            {selectedIndex + 1} / {displayableRebrands.length}
          </span>
        </div>
      </div>
      
      {isSessionComplete && onRetry && (
        <div className="flex justify-center pt-4">
           <Button variant="ghost" onClick={onRetry} className="gap-2 text-gray-500 hover:text-gray-900">
             <RefreshCw size={14} />
             Relancer
           </Button>
        </div>
      )}
    </div>
  );
}
