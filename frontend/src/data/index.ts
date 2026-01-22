/**
 * Data types re-exported for backward compatibility.
 * The actual data loading is now handled by hooks (useCategoryData, useCategories).
 *
 * @deprecated Use types from '../types' and hooks from '../hooks' instead.
 */

// Re-export types for backward compatibility
export type {
  ColorEntry,
  EyeTracking,
  ChromaticMapping,
  TextualInventory,
  AssetSymbolism,
  VisualAnalysis,
  PodScore,
  PopStatus,
  Product,
  StrategicInsight,
  PointOfDifference,
  PointOfParity,
  CategoryOverview,
  CategoryListItem,
  CategoryData,
} from '../types';

// Legacy exports - these are no longer used directly
// Data is now loaded dynamically via hooks

/**
 * @deprecated Use useCategoryData hook instead
 */
export const products: never[] = [];

/**
 * @deprecated Use useCategoryData hook instead
 */
export const categoryName = '';

/**
 * @deprecated Use useCategoryData hook instead
 */
export const categorySummary = '';

/**
 * @deprecated Use useCategoryData hook instead
 */
export const strategicInsights: never[] = [];

/**
 * @deprecated Use useCategoryData hook instead
 */
export const pointsOfDifference: never[] = [];

/**
 * @deprecated Use useCategoryData hook instead
 */
export const pointsOfParity: never[] = [];

/**
 * @deprecated Use useCategoryData hook instead
 */
export const axisDescriptions: Record<string, string> = {};

// Legacy functions - kept for any code that might still reference them

/**
 * @deprecated Use useCategoryData hook instead
 */
export async function loadCategoryData(categoryId?: string): Promise<{
  overview: any;
  products: any[];
}> {
  console.warn('loadCategoryData is deprecated. Use useCategoryData hook instead.');
  const { api } = await import('../api/client');

  // If no categoryId, find lait d'avoine
  if (!categoryId) {
    const { categories } = await api.categories.list();
    const laitDavoine = categories.find((c: any) => c.name === "lait d'avoine");
    if (!laitDavoine) {
      throw new Error('No "lait d\'avoine" category found');
    }
    categoryId = laitDavoine.id;
  }

  const [overview, { products }] = await Promise.all([
    api.categories.get(categoryId!),
    api.categories.getProducts(categoryId!),
  ]);

  return { overview, products };
}

/**
 * @deprecated Use useCategoryData hook instead
 */
export function getProducts() {
  console.warn('getProducts is deprecated. Use useCategoryData hook instead.');
  return [];
}

/**
 * @deprecated Use useCategoryData hook instead
 */
export function getCategoryName() {
  console.warn('getCategoryName is deprecated. Use useCategoryData hook instead.');
  return '';
}

/**
 * @deprecated Use useCategoryData hook instead
 */
export function getCategorySummary() {
  console.warn('getCategorySummary is deprecated. Use useCategoryData hook instead.');
  return '';
}

/**
 * @deprecated Use useCategoryData hook instead
 */
export function getStrategicInsights() {
  console.warn('getStrategicInsights is deprecated. Use useCategoryData hook instead.');
  return [];
}

/**
 * @deprecated Use useCategoryData hook instead
 */
export function getPointsOfDifference() {
  console.warn('getPointsOfDifference is deprecated. Use useCategoryData hook instead.');
  return [];
}

/**
 * @deprecated Use useCategoryData hook instead
 */
export function getPointsOfParity() {
  console.warn('getPointsOfParity is deprecated. Use useCategoryData hook instead.');
  return [];
}

/**
 * @deprecated Use useCategoryData hook instead
 */
export function getAxisDescriptions() {
  console.warn('getAxisDescriptions is deprecated. Use useCategoryData hook instead.');
  return {};
}
