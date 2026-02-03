import React, { useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Upload, Image as ImageIcon, Sparkles, X, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import { Footer } from '../components/atoms';

/**
 * Single image upload page for visual analysis.
 * Allows users to upload a product image and get detailed visual analysis.
 */
export function SingleImageAnalysis() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [brand, setBrand] = useState('');
  const [productName, setProductName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileSelect = useCallback((selectedFile: File) => {
    // Validate file type
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(selectedFile.type)) {
      setError('Format non supporté. Utilisez PNG, JPG, GIF ou WebP.');
      return;
    }

    // Validate file size (max 10MB)
    if (selectedFile.size > 10 * 1024 * 1024) {
      setError('Image trop volumineuse. Maximum 10 Mo.');
      return;
    }

    setFile(selectedFile);
    setError(null);

    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreview(reader.result as string);
    };
    reader.readAsDataURL(selectedFile);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  }, [handleFileSelect]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      handleFileSelect(selectedFile);
    }
  };

  const clearFile = () => {
    setFile(null);
    setPreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file) {
      setError('Veuillez sélectionner une image');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.imageAnalysis.upload(
        file,
        brand.trim() || undefined,
        productName.trim() || undefined
      );
      
      // Redirect to result page
      navigate(`/analyze/${response.job_id}`);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Erreur lors du téléchargement');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col font-sans">
      {/* Main content */}
      <div className="flex-1 p-8 md:p-12">
        <div className="max-w-2xl mx-auto space-y-8">
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
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-50 border border-purple-100 text-purple-600 text-xs font-bold uppercase tracking-wider shadow-sm">
              <ImageIcon size={12} />
              Analyse Visuelle
            </div>
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900">
              Analyser une image produit
            </h1>
            <p className="text-gray-500">
              Téléchargez une image de packaging pour obtenir une analyse visuelle complète par IA.
            </p>
          </header>

          {/* Upload Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Drop Zone */}
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onClick={() => fileInputRef.current?.click()}
              className={`
                relative cursor-pointer rounded-2xl border-2 border-dashed transition-all duration-300
                ${isDragging 
                  ? 'border-purple-400 bg-purple-50/50' 
                  : 'border-gray-200 hover:border-purple-300 hover:bg-purple-50/30'
                }
                ${preview ? 'p-4' : 'p-12'}
              `}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg,image/jpg,image/gif,image/webp"
                onChange={handleFileInputChange}
                className="hidden"
              />

              {preview ? (
                <div className="relative">
                  <img
                    src={preview}
                    alt="Preview"
                    className="w-full h-64 object-contain rounded-xl bg-white/50"
                  />
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      clearFile();
                    }}
                    className="absolute top-2 right-2 p-2 bg-white/90 hover:bg-white rounded-full shadow-md transition-colors"
                  >
                    <X size={16} className="text-gray-600" />
                  </button>
                  <div className="mt-3 text-center text-sm text-gray-500">
                    {file?.name}
                  </div>
                </div>
              ) : (
                <div className="text-center">
                  <div className="mx-auto w-16 h-16 rounded-2xl bg-purple-100/50 flex items-center justify-center mb-4">
                    <Upload className="w-8 h-8 text-purple-400" />
                  </div>
                  <p className="text-gray-700 font-medium mb-1">
                    Glissez-déposez votre image ici
                  </p>
                  <p className="text-sm text-gray-400">
                    ou cliquez pour sélectionner un fichier
                  </p>
                  <p className="text-xs text-gray-400 mt-3">
                    PNG, JPG, GIF ou WebP • Max 10 Mo
                  </p>
                </div>
              )}
            </div>

            {/* Optional Fields */}
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="brand" className="block text-sm font-medium text-gray-700 mb-2">
                  Marque (optionnel)
                </label>
                <input
                  type="text"
                  id="brand"
                  value={brand}
                  onChange={(e) => setBrand(e.target.value)}
                  placeholder="Ex: Diptyque"
                  className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-300 transition-all"
                />
              </div>
              <div>
                <label htmlFor="productName" className="block text-sm font-medium text-gray-700 mb-2">
                  Nom du produit (optionnel)
                </label>
                <input
                  type="text"
                  id="productName"
                  value={productName}
                  onChange={(e) => setProductName(e.target.value)}
                  placeholder="Ex: Bougie Baies 190g"
                  className="w-full px-4 py-3 rounded-xl border border-gray-200 bg-white/50 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-300 transition-all"
                />
              </div>
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
              disabled={loading || !file}
              whileHover={{ scale: loading || !file ? 1 : 1.02 }}
              whileTap={{ scale: loading || !file ? 1 : 0.98 }}
              className={`
                w-full py-4 px-6 rounded-xl font-semibold text-white
                flex items-center justify-center gap-3
                transition-all duration-300 shadow-lg
                ${loading || !file
                  ? 'bg-gray-300 cursor-not-allowed'
                  : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 hover:shadow-purple-500/25'
                }
              `}
            >
              {loading ? (
                <>
                  <motion.div 
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  >
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full" />
                  </motion.div>
                  <span>Envoi en cours...</span>
                </>
              ) : (
                <>
                  <Sparkles size={20} />
                  <span>Lancer l'analyse visuelle</span>
                </>
              )}
            </motion.button>
          </form>

          {/* Info Section */}
          <div className="bg-white/40 backdrop-blur-sm rounded-2xl border border-white/50 p-6 shadow-sm">
            <h3 className="font-semibold text-gray-900 mb-3">Ce que vous obtiendrez :</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-start gap-2">
                <span className="text-purple-500 mt-0.5">•</span>
                <span>Analyse de la hiérarchie visuelle et des éléments dominants</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-500 mt-0.5">•</span>
                <span>Simulation du parcours oculaire (eye-tracking)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-500 mt-0.5">•</span>
                <span>Palette chromatique complète avec codes couleurs</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-500 mt-0.5">•</span>
                <span>Inventaire typographique et analyse des claims</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-500 mt-0.5">•</span>
                <span>Analyse des symboles de confiance et certifications</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Footer */}
      <Footer variant="light" />
    </div>
  );
}
