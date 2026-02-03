import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Upload, Sparkles, ImageIcon, FileText, AlertCircle, ArrowRight, Check } from 'lucide-react';
import { Button } from '../atoms';
import { api } from '../../api/client';
import { cn } from '../../lib/utils';

type RebrandSessionModalProps = {
  isOpen: boolean;
  onClose: () => void;
  analysisId: string;
  category: string;
  productCount: number;
  onSessionStarted: (sessionId: string) => void;
};

export function RebrandSessionModal({
  isOpen,
  onClose,
  analysisId,
  category,
  productCount,
  onSessionStarted,
}: RebrandSessionModalProps) {
  const [sourceFile, setSourceFile] = useState<File | null>(null);
  const [sourcePreview, setSourcePreview] = useState<string | null>(null);
  const [brandIdentity, setBrandIdentity] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileSelect = useCallback((file: File) => {
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      setError('Format non supporté. Utilisez PNG, JPG, GIF ou WEBP.');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError('Image trop grande. Maximum 10MB.');
      return;
    }

    setError(null);
    setSourceFile(file);

    const reader = new FileReader();
    reader.onloadend = () => {
      setSourcePreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
  }, [handleFileSelect]);

  const handleSubmit = async () => {
    if (!sourceFile || !brandIdentity.trim()) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await api.rebrandSession.start(
        analysisId,
        sourceFile,
        brandIdentity,
        category
      );
      onSessionStarted(response.session_id);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Une erreur est survenue.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetForm = () => {
    setSourceFile(null);
    setSourcePreview(null);
    setBrandIdentity('');
    setError(null);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-white/20 backdrop-blur-md"
            onClick={() => !isSubmitting && onClose()}
          />

          <motion.div
            initial={{ scale: 0.95, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 20 }}
            className="relative w-full max-w-2xl bg-white/80 backdrop-blur-xl border border-white/60 shadow-2xl rounded-3xl overflow-hidden flex flex-col max-h-[90vh]"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 md:p-8 border-b border-gray-100/50">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <div className="p-2 bg-purple-100 rounded-lg text-purple-600">
                    <Sparkles size={20} />
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900">Rebranding IA</h2>
                </div>
                <p className="text-gray-500">
                  Générez <span className="font-semibold text-purple-600">{productCount} variations</span> de votre produit basées sur le marché.
                </p>
              </div>
              <button
                onClick={onClose}
                disabled={isSubmitting}
                className="p-2 hover:bg-gray-100 rounded-full text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X size={24} />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-8">
              {/* Image Upload Section */}
              <div className="space-y-4">
                <label className="flex items-center gap-2 text-sm font-semibold text-gray-700">
                  <ImageIcon size={16} className="text-purple-500" />
                  1. Votre Produit Actuel
                </label>
                
                <div
                  onDrop={handleDrop}
                  onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                  onDragLeave={(e) => { e.preventDefault(); setIsDragging(false); }}
                  className={cn(
                    "relative group cursor-pointer transition-all duration-300",
                    "border-2 border-dashed rounded-2xl p-8 text-center",
                    isDragging ? "border-purple-500 bg-purple-50" : "border-gray-200 hover:border-purple-300 hover:bg-white/50",
                    sourcePreview ? "bg-white/40 border-solid border-gray-200" : "bg-white/30"
                  )}
                >
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                    disabled={isSubmitting}
                  />

                  {sourcePreview ? (
                    <div className="flex items-center gap-6">
                      <div className="relative w-24 h-24 rounded-xl overflow-hidden shadow-sm border border-white">
                        <img src={sourcePreview} alt="Preview" className="w-full h-full object-contain bg-white" />
                      </div>
                      <div className="flex-1 text-left">
                        <p className="font-medium text-gray-900">{sourceFile?.name}</p>
                        <p className="text-sm text-gray-500 mb-2">{(sourceFile!.size / (1024 * 1024)).toFixed(2)} MB</p>
                        <span className="text-sm text-purple-600 font-medium hover:text-purple-700">
                          Changer l'image
                        </span>
                      </div>
                      <div className="p-2 bg-green-100 text-green-600 rounded-full">
                        <Check size={20} />
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <div className="w-12 h-12 bg-purple-100 text-purple-500 rounded-full flex items-center justify-center mx-auto transition-transform group-hover:scale-110">
                        <Upload size={24} />
                      </div>
                      <div>
                        <p className="text-lg font-medium text-gray-700">Glissez votre image ici</p>
                        <p className="text-sm text-gray-400">ou cliquez pour parcourir (PNG, JPG, WebP)</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Brand Identity Section */}
              <div className="space-y-4">
                <label className="flex items-center gap-2 text-sm font-semibold text-gray-700">
                  <FileText size={16} className="text-purple-500" />
                  2. Identité & Contraintes
                </label>
                
                <div className="relative">
                  <textarea
                    value={brandIdentity}
                    onChange={(e) => setBrandIdentity(e.target.value)}
                    disabled={isSubmitting}
                    placeholder="Décrivez votre marque : couleurs, style, éléments obligatoires..."
                    className="w-full h-40 px-5 py-4 bg-white/40 border border-gray-200 rounded-2xl text-gray-700 placeholder-gray-400 focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500 transition-all resize-none glass-input"
                  />
                  <div className="absolute bottom-4 right-4 text-xs text-gray-400 bg-white/80 px-2 py-1 rounded-md backdrop-blur-sm">
                    {brandIdentity.length} chars
                  </div>
                </div>
                
                <div className="bg-blue-50/50 border border-blue-100 rounded-xl p-4 flex gap-3">
                  <div className="flex-shrink-0 mt-0.5">
                    <Sparkles size={16} className="text-blue-500" />
                  </div>
                  <p className="text-sm text-blue-700/80 leading-relaxed">
                    L'IA va adapter votre produit au style de chaque concurrent tout en respectant ces contraintes pour créer des variations uniques.
                  </p>
                </div>
              </div>

              {error && (
                <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-100 rounded-xl text-red-600">
                  <AlertCircle size={20} className="flex-shrink-0" />
                  <p className="text-sm font-medium">{error}</p>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-6 md:p-8 bg-gray-50/50 border-t border-gray-100 flex items-center justify-end gap-4">
              <Button 
                variant="ghost" 
                onClick={onClose} 
                disabled={isSubmitting}
              >
                Annuler
              </Button>
              <Button
                variant="primary"
                onClick={handleSubmit}
                disabled={!sourceFile || !brandIdentity.trim()}
                loading={isSubmitting}
                className="px-8"
              >
                {isSubmitting ? 'Lancement...' : 'Lancer le Rebranding'}
                {!isSubmitting && <ArrowRight size={18} />}
              </Button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
