import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GlassCard } from './GlassCard';
import { GlassButton } from './GlassButton';
import { GlassInput } from './GlassInput';
import { X, Mail, AlertCircle } from 'lucide-react';

interface EmailModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (email: string) => void;
  canClose?: boolean;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export const EmailModal: React.FC<EmailModalProps> = ({ 
    isOpen, 
    onClose, 
    onSuccess,
    canClose = true 
}) => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
        setError("L'adresse email est requise");
        return;
    }
    
    setLoading(true);
    setError(null);
    
    // We validate here for immediate feedback, but the actual job start 
    // (which also validates) happens in the parent component via onSuccess
    try {
      const response = await fetch(`${API_URL}/api/email/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || 'La validation a échoué');
      }
      
      onSuccess(email);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Une erreur est survenue");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={canClose ? onClose : undefined}
          />
          
          <motion.div
            initial={{ scale: 0.95, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 20 }}
            className="relative w-full max-w-md z-50"
          >
            <GlassCard className="bg-white/90 shadow-2xl">
              {canClose && (
                <button 
                    onClick={onClose}
                    className="absolute top-4 right-4 text-black/40 hover:text-black transition-colors"
                >
                    <X size={20} />
                </button>
              )}
              
              <div className="text-center mb-6">
                <div className="mx-auto w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mb-4 text-purple-600">
                  <Mail size={24} />
                </div>
                <h3 className="text-xl font-bold text-gray-900">Entrez votre email professionnel</h3>
                <p className="text-gray-500 text-sm mt-2">
                  Veuillez fournir votre email professionnel pour lancer l'analyse.
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <GlassInput
                    type="email"
                    placeholder="nom@entreprise.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    autoFocus
                    label="Email professionnel"
                />
                
                {error && (
                    <div className="flex items-center gap-2 text-sm text-red-500 bg-red-50 p-3 rounded-lg border border-red-100">
                        <AlertCircle size={16} />
                        {error}
                    </div>
                )}
                
                <GlassButton 
                    type="submit" 
                    className="w-full"
                    isLoading={loading}
                >
                    Lancer l'analyse
                </GlassButton>
              </form>
            </GlassCard>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
