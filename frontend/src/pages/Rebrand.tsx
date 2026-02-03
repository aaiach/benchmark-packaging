import React, { useState, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, ArrowLeft, ArrowRight, Upload, X, Image as ImageIcon } from 'lucide-react';
import { api } from '../api/client';
import { Footer } from '../components/atoms';

/**
 * Image upload component with drag & drop support
 */
function ImageUploadZone({
  label,
  sublabel,
  file,
  preview,
  onFileSelect,
  onClear,
  accentColor = 'purple',
  icon,
}: {
  label: string;
  sublabel: string;
  file: File | null;
  preview: string | null;
  onFileSelect: (file: File) => void;
  onClear: () => void;
  accentColor?: 'purple' | 'pink';
  icon: string;
}) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type.startsWith('image/')) {
      onFileSelect(droppedFile);
    }
  }, [onFileSelect]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      onFileSelect(selectedFile);
    }
  }, [onFileSelect]);

  const ringColor = accentColor === 'purple' ? 'ring-purple-200 border-purple-300' : 'ring-pink-200 border-pink-300';
  const bgHover = accentColor === 'purple' ? 'hover:border-purple-300 hover:bg-purple-50/50' : 'hover:border-pink-300 hover:bg-pink-50/50';
  const dragBg = accentColor === 'purple' ? 'border-purple-400 bg-purple-50' : 'border-pink-400 bg-pink-50';

  return (
    <div className="space-y-4">
      <label className="block text-sm font-semibold text-gray-700">
        {label} <span className="text-gray-400 font-normal">({sublabel})</span>
      </label>
      
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          relative aspect-square rounded-xl border-2 border-dashed 
          transition-all duration-200 overflow-hidden
          ${preview 
            ? 'border-gray-200 bg-gray-50' 
            : isDragging 
              ? dragBg
              : `border-gray-200 bg-gray-50 ${bgHover} cursor-pointer`
          }
        `}
      >
        {preview ? (
          <>
            <img
              src={preview}
              alt="Preview"
              className="w-full h-full object-contain p-4"
            />
            <button
              onClick={(e) => { e.stopPropagation(); onClear(); }}
              className="absolute top-3 right-3 p-2 bg-white/90 hover:bg-white rounded-full shadow-md transition-colors"
            >
              <X size={16} className="text-gray-600" />
            </button>
            <div className="absolute bottom-3 left-3 right-3 px-3 py-2 bg-white/90 rounded-lg text-xs text-gray-600 truncate">
              {file?.name}
            </div>
          </>
        ) : (
          <label className="absolute inset-0 flex flex-col items-center justify-center cursor-pointer">
            <input
              type="file"
              accept="image/*"
              onChange={handleFileInput}
              className="hidden"
            />
            <div className="text-4xl mb-3">{icon}</div>
            <Upload size={24} className="text-gray-400 mb-2" />
            <div className="text-sm text-gray-500 font-medium">
              Glisser-déposer ou cliquer
            </div>
            <div className="text-xs text-gray-400 mt-1">
              PNG, JPG, WEBP
            </div>
          </label>
        )}
      </div>
    </div>
  );
}

/**
 * Rebrand page for uploading source and inspiration images.
 */
export function Rebrand() {
  const navigate = useNavigate();
  
  const [sourceFile, setSourceFile] = useState<File | null>(null);
  const [sourcePreview, setSourcePreview] = useState<string | null>(null);
  const [inspirationFile, setInspirationFile] = useState<File | null>(null);
  const [inspirationPreview, setInspirationPreview] = useState<string | null>(null);
  
  const [brandIdentity, setBrandIdentity] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSourceSelect = useCallback((file: File) => {
    setSourceFile(file);
    setSourcePreview(URL.createObjectURL(file));
    setError(null);
  }, []);

  const handleInspirationSelect = useCallback((file: File) => {
    setInspirationFile(file);
    setInspirationPreview(URL.createObjectURL(file));
    setError(null);
  }, []);

  const clearSource = useCallback(() => {
    if (sourcePreview) URL.revokeObjectURL(sourcePreview);
    setSourceFile(null);
    setSourcePreview(null);
  }, [sourcePreview]);

  const clearInspiration = useCallback(() => {
    if (inspirationPreview) URL.revokeObjectURL(inspirationPreview);
    setInspirationFile(null);
    setInspirationPreview(null);
  }, [inspirationPreview]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!sourceFile) {
      setError('Veuillez sélectionner une image source');
      return;
    }
    if (!inspirationFile) {
      setError('Veuillez sélectionner une image d\'inspiration');
      return;
    }
    if (!brandIdentity.trim()) {
      setError('Veuillez décrire l\'identité de marque / contraintes');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const response = await api.rebrand.start(sourceFile, inspirationFile, brandIdentity.trim());
      navigate(`/rebrand/${response.job_id}`);
    } catch (err: any) {
      setError(err.message || 'Erreur lors du lancement du rebranding');
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col font-sans">
      <div className="flex-1 p-8 md:p-12">
        <div className="max-w-5xl mx-auto space-y-8">
          {/* Back link */}
          <Link 
            to="/" 
            className="inline-flex items-center gap-2 text-gray-500 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft size={16} />
            <span className="text-sm font-medium">Retour</span>
          </Link>

          {/* Header */}
          <header className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-100 text-purple-600 text-xs font-bold uppercase tracking-wider shadow-sm">
              <Sparkles size={12} />
              Rebranding IA
            </div>
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900">
              Transformer un packaging
            </h1>
            <p className="text-gray-500 max-w-2xl">
              Uploadez votre packaging source et un design d'inspiration. Notre IA combinera vos éléments de marque avec le style visuel de l'inspiration.
            </p>
          </header>

          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Image Upload Grid */}
            <div className="grid md:grid-cols-2 gap-8">
              {/* Source Upload */}
              <ImageUploadZone
                label="Image Source"
                sublabel="votre produit à rebrander"
                file={sourceFile}
                preview={sourcePreview}
                onFileSelect={handleSourceSelect}
                onClear={clearSource}
                accentColor="purple"
                icon="📦"
              />

              {/* Inspiration Upload */}
              <ImageUploadZone
                label="Image Inspiration"
                sublabel="design de référence"
                file={inspirationFile}
                preview={inspirationPreview}
                onFileSelect={handleInspirationSelect}
                onClear={clearInspiration}
                accentColor="pink"
                icon="✨"
              />
            </div>

            {/* Arrow between selections */}
            {sourceFile && inspirationFile && (
              <div className="flex items-center justify-center gap-4 py-4">
                <div className="text-center">
                  <div className="text-sm text-gray-500 mb-2">Transformation</div>
                  <div className="flex items-center gap-3 text-purple-600">
                    <ImageIcon size={20} />
                    <span className="font-medium">Source</span>
                    <ArrowRight size={20} />
                    <span className="font-medium">Style de l'inspiration</span>
                    <ImageIcon size={20} />
                  </div>
                </div>
              </div>
            )}

            {/* Brand Identity Input */}
            <div className="space-y-3">
              <label className="block text-sm font-semibold text-gray-700">
                Identité de marque & Contraintes
              </label>
              <textarea
                value={brandIdentity}
                onChange={(e) => setBrandIdentity(e.target.value)}
                placeholder={`Décrivez votre marque et les éléments à conserver:

• Nom de marque: [votre marque]
• Nom du produit: [nom du produit]
• Couleurs principales: [ex: noir dominant, accents dorés]
• Logo: [description ou "conserver l'apparence actuelle"]

Trust marks / Claims disponibles:
• Sans sucre ajouté
• 100% végétal
• Bio certifié
• ...

Autres contraintes:
• Le format exact du packaging doit être conservé
• ...`}
                rows={12}
                className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-300 transition-all resize-none font-mono text-sm"
              />
              <p className="text-xs text-gray-400">
                Décrivez précisément votre marque, les éléments à conserver (logo, couleurs, claims) et les contraintes.
              </p>
            </div>

            {/* Error Message */}
            {error && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center text-red-500 text-sm bg-red-50/80 backdrop-blur-sm py-3 rounded-xl border border-red-100/50 shadow-sm"
              >
                {error}
              </motion.div>
            )}

            {/* Submit Button */}
            <motion.button
              type="submit"
              disabled={submitting || !sourceFile || !inspirationFile || !brandIdentity.trim()}
              whileHover={{ scale: submitting ? 1 : 1.02 }}
              whileTap={{ scale: submitting ? 1 : 0.98 }}
              className={`
                w-full py-4 px-6 rounded-xl font-semibold text-white
                flex items-center justify-center gap-3
                transition-all duration-300 shadow-lg
                ${submitting || !sourceFile || !inspirationFile || !brandIdentity.trim()
                  ? 'bg-gray-300 cursor-not-allowed'
                  : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 hover:shadow-purple-500/25'
                }
              `}
            >
              {submitting ? (
                <>
                  <motion.div 
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  >
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full" />
                  </motion.div>
                  <span>Lancement du rebranding...</span>
                </>
              ) : (
                <>
                  <Sparkles size={20} />
                  <span>Générer le nouveau packaging</span>
                </>
              )}
            </motion.button>
          </form>

          {/* Info Section */}
          <div className="bg-white/40 backdrop-blur-sm rounded-2xl border border-white/50 p-6 shadow-sm">
            <h3 className="font-semibold text-gray-900 mb-3">Comment ça marche :</h3>
            <ol className="space-y-2 text-sm text-gray-600 list-decimal list-inside">
              <li>Uploadez votre packaging actuel (source) et un design qui vous inspire</li>
              <li>Décrivez votre identité de marque et les éléments à conserver</li>
              <li>Notre IA analyse les deux images et génère un nouveau packaging combinant votre marque avec le style de l'inspiration</li>
            </ol>
          </div>
        </div>
      </div>

      <Footer variant="light" />
    </div>
  );
}
