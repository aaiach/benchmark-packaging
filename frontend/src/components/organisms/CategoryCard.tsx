import React from 'react';
import { Link } from 'react-router-dom';
import { Eye, BarChart3, Calendar, Package } from 'lucide-react';
import { cn } from '../../lib/utils';
import { Card, Badge } from '../atoms';
import { formatDate } from '../../lib/utils';
import type { CategoryListItem } from '../../types';

type CategoryCardProps = {
  category: CategoryListItem;
};

/**
 * Card for displaying a category in the list.
 */
export function CategoryCard({ category }: CategoryCardProps) {
  return (
    <Link to={`/category/${category.id}`}>
      <Card className="hover:bg-white/10 transition-colors cursor-pointer group">
        <div className="flex items-start justify-between mb-4">
          <h3 className="text-lg font-bold text-white capitalize group-hover:text-blue-300 transition-colors">
            {category.name}
          </h3>
          <div className="flex gap-1">
            {category.has_visual_analysis && (
              <Badge variant="success" className="text-[10px]">
                <Eye size={10} />
                Visuel
              </Badge>
            )}
            {category.has_competitive_analysis && (
              <Badge variant="info" className="text-[10px]">
                <BarChart3 size={10} />
                Concurrentiel
              </Badge>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="flex items-center gap-2 text-gray-400">
            <Package size={14} />
            <span>{category.product_count} produits</span>
          </div>
          <div className="flex items-center gap-2 text-gray-400">
            <Calendar size={14} />
            <span>{formatDate(category.analysis_date)}</span>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-white/10">
          <span className="text-xs text-gray-500">ID d'exécution : {category.run_id}</span>
        </div>
      </Card>
    </Link>
  );
}
