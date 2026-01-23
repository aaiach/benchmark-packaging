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
      <Card className="hover:bg-white/60 hover:shadow-glass-lg hover:-translate-y-1 transition-all cursor-pointer group border-white/60">
        <div className="flex items-start justify-between mb-4">
          <h3 className="text-lg font-bold text-gray-900 capitalize group-hover:text-blue-600 transition-colors">
            {category.name}
          </h3>
          <div className="flex gap-1.5">
            {category.has_visual_analysis && (
              <Badge variant="success" className="text-[10px] px-2">
                <Eye size={10} className="mr-1" />
                Visuel
              </Badge>
            )}
            {category.has_competitive_analysis && (
              <Badge variant="info" className="text-[10px] px-2">
                <BarChart3 size={10} className="mr-1" />
                Concurrentiel
              </Badge>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="flex items-center gap-2 text-gray-500">
            <Package size={14} className="text-gray-400" />
            <span>{category.product_count} produits</span>
          </div>
          <div className="flex items-center gap-2 text-gray-500">
            <Calendar size={14} className="text-gray-400" />
            <span>{formatDate(category.analysis_date)}</span>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-gray-100">
          <span className="text-xs text-gray-400 font-mono">ID: {category.run_id}</span>
        </div>
      </Card>
    </Link>
  );
}
