import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { GlassCard } from './GlassCard';
import { api } from '../../api/client';
import { LANDING_EXAMPLES } from '../../config/landingExamples';
import { Loader2, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { LANDING_CONTENT } from '../content';

interface ExampleData {
  id: string;
  name: string;
  summary: string;
  imageUrl: string | null;
  productCount: number;
}

export const ExampleCards: React.FC = () => {
  const [examples, setExamples] = useState<ExampleData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchExamples = async () => {
      try {
        const results = await Promise.all(
          LANDING_EXAMPLES.map(async (id) => {
            try {
              const [category, products] = await Promise.all([
                api.categories.get(id),
                api.categories.getProducts(id)
              ]);

              const firstProduct = products.products && products.products.length > 0 
                ? products.products[0] 
                : null;

              return {
                id: category.id,
                name: category.name,
                summary: category.summary,
                imageUrl: firstProduct ? firstProduct.image : null,
                productCount: category.product_count
              };
            } catch (err) {
              console.error(`Failed to fetch example ${id}`, err);
              return null;
            }
          })
        );
        
        setExamples(results.filter((ex): ex is ExampleData => ex !== null));
      } catch (err) {
        console.error("Failed to fetch examples", err);
      } finally {
        setLoading(false);
      }
    };

    fetchExamples();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-black/20" />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-6xl mx-auto px-4">
      {examples.map((example, index) => (
        <Link to={`/category/${example.id}`} key={example.id} className="block group">
          <GlassCard className="h-full hover:scale-[1.02] transition-transform duration-300" hoverEffect>
            <div className="aspect-[4/3] w-full overflow-hidden rounded-xl mb-4 bg-white/50 relative">
              {example.imageUrl ? (
                <img 
                  src={example.imageUrl} 
                  alt={example.name}
                  className="w-full h-full object-contain p-4 mix-blend-multiply transition-transform duration-700 group-hover:scale-110"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-black/20">
                  {LANDING_CONTENT.cards.noImage}
                </div>
              )}
              <div className="absolute top-3 right-3 bg-black/5 backdrop-blur-md px-2 py-1 rounded-lg text-xs font-medium text-black/60">
                {example.productCount} {LANDING_CONTENT.cards.productsCountSuffix}
              </div>
            </div>
            
            <h3 className="text-lg font-medium text-black mb-2 capitalize group-hover:text-purple-600 transition-colors">
              {example.name}
            </h3>
            
            <p className="text-sm text-black/50 line-clamp-3 leading-relaxed mb-4">
              {example.summary || LANDING_CONTENT.cards.defaultSummary}
            </p>

            <div className="flex items-center text-xs font-medium text-black/40 group-hover:text-black/80 transition-colors mt-auto">
              {LANDING_CONTENT.cards.viewAnalysis} <ArrowRight className="w-3 h-3 ml-1 transition-transform group-hover:translate-x-1" />
            </div>
          </GlassCard>
        </Link>
      ))}
    </div>
  );
};
