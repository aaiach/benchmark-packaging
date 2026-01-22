import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';
import type { CategoryListItem } from '../types';

type UseCategoriesResult = {
  categories: CategoryListItem[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
};

/**
 * Hook for loading the list of available categories.
 */
export function useCategories(): UseCategoriesResult {
  const [categories, setCategories] = useState<CategoryListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCategories = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const { categories: data } = await api.categories.list();
      setCategories(data as CategoryListItem[]);
    } catch (err: any) {
      setError(err.message || 'Failed to load categories');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  return { categories, loading, error, refetch: fetchCategories };
}
