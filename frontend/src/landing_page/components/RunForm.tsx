import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Play, Sparkles } from 'lucide-react';
import { GlassCard } from './GlassCard';
import { GlassButton } from './GlassButton';
import { GlassInput } from './GlassInput';
import { api } from '../../api/client';
import { LANDING_CONTENT } from '../content';

export const RunForm: React.FC = () => {
  const navigate = useNavigate();
  const [category, setCategory] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!category.trim()) {
      setError(LANDING_CONTENT.runForm.errors.emptyCategory);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.scraper.run({
        category: category.trim(),
        country: 'France',
        count: 6,
        steps: '1-7'
      });
      
      navigate(`/jobs/${response.job_id}`);
    } catch (err: any) {
      console.error(err);
      setError(err.message || LANDING_CONTENT.runForm.errors.generic);
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto relative z-10">
       <form onSubmit={handleSubmit} className="relative">
         <div className="relative group">
            {/* Input Wrapper with Gradient Border on Focus */}
            <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-200 to-pink-200 rounded-2xl blur opacity-30 group-hover:opacity-60 transition duration-500"></div>
            
            <div className="relative flex items-center bg-white/40 backdrop-blur-xl rounded-2xl border border-white/50 shadow-[0_8px_32px_rgba(0,0,0,0.05)] transition-all duration-300 focus-within:bg-white/60 focus-within:shadow-[0_12px_40px_rgba(0,0,0,0.08)] focus-within:scale-[1.01]">
                <input
                    type="text"
                    className="w-full bg-transparent border-none px-6 py-5 text-xl font-light text-black placeholder-black/30 focus:outline-none focus:ring-0"
                    placeholder={LANDING_CONTENT.runForm.inputLabel}
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    autoFocus
                />
                
                <div className="pr-2">
                    <motion.button 
                      type="submit" 
                      disabled={loading}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="group relative h-14 w-14 rounded-xl overflow-hidden shadow-lg hover:shadow-purple-500/25 transition-shadow duration-300"
                    >
                        {/* Animated Gradient Background */}
                        <div className="absolute inset-0 bg-gradient-to-tr from-black via-gray-900 to-black group-hover:from-purple-600 group-hover:via-pink-600 group-hover:to-orange-500 transition-colors duration-500" />
                        
                        {/* Shine Effect */}
                        <div className="absolute inset-0 opacity-0 group-hover:opacity-20 bg-gradient-to-r from-transparent via-white to-transparent -skew-x-12 translate-x-[-100%] group-hover:animate-shine" />

                        {/* Content */}
                        <div className="relative flex items-center justify-center h-full w-full text-white">
                           {loading ? (
                             <motion.div 
                               animate={{ rotate: 360 }}
                               transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                             >
                               <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full" />
                             </motion.div>
                           ) : (
                             <Sparkles className="w-6 h-6 text-white/90 group-hover:text-white transition-colors" strokeWidth={1.5} />
                           )}
                        </div>
                    </motion.button>
                </div>
            </div>
         </div>

         {error && (
           <motion.div 
             initial={{ opacity: 0, y: 10 }}
             animate={{ opacity: 1, y: 0 }}
             className="absolute top-full left-0 right-0 mt-3 text-center text-red-500 text-sm bg-red-50/80 backdrop-blur-sm py-2 rounded-lg border border-red-100/50 shadow-sm"
           >
             {error}
           </motion.div>
         )}
       </form>
    </div>
  );
};
