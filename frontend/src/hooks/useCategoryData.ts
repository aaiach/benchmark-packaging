import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';
import type { CategoryData, CategoryOverview, Product } from '../types';

type UseCategoryDataResult = {
  data: CategoryData | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
};

/**
 * Hook for loading category data (overview + products).
 *
 * @param categoryId - Category ID to load, or null to find default
 */
export function useCategoryData(categoryId: string | null): UseCategoryDataResult {
  const [data, setData] = useState<CategoryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      let targetId = categoryId;

      // If no categoryId provided, find "lait d'avoine" category
      if (!targetId) {
        const { categories } = await api.categories.list();
        const laitDavoine = categories.find((c) => c.name === "lait d'avoine");

        if (!laitDavoine) {
          throw new Error('No "lait d\'avoine" category found');
        }

        targetId = laitDavoine.id;
      }

      // Load overview and products in parallel
      const [overview, { products }] = await Promise.all([
        api.categories.get(targetId!) as Promise<CategoryOverview>,
        api.categories.getProducts(targetId!) as Promise<{ products: Product[] }>,
      ]);

      setData({ overview, products });
    } catch (err: any) {
      setError(err.message || 'Failed to load category data');
    } finally {
      setLoading(false);
    }
  }, [categoryId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}
