/**
 * API client for backend communication.
 *
 * This module provides typed methods for all backend API endpoints.
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Unknown error' }));
      throw new ApiError(response.status, error.error || response.statusText);
    }

    return response.json();
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(0, 'Network error - could not connect to API server');
  }
}

// Category endpoints
export const api = {
  categories: {
    /**
     * List all available categories
     */
    list: () => request<{ categories: any[] }>('/api/categories'),

    /**
     * Get category overview with PODs, POPs, and insights
     */
    get: (id: string) => request<any>(`/api/categories/${id}`),

    /**
     * Get all products for a category
     */
    getProducts: (id: string) => request<{ products: any[] }>(`/api/categories/${id}/products`),

    /**
     * Get single product with full visual analysis
     */
    getProduct: (categoryId: string, productId: string) =>
      request<any>(`/api/categories/${categoryId}/products/${productId}`),
  },

  scraper: {
    /**
     * Initialize scraper job (Draft mode)
     */
    init: (params: { category: string; country?: string; count?: number; steps?: string }) =>
      request<{ job_id: string; status: string }>('/api/scraper/init', {
        method: 'POST',
        body: JSON.stringify(params),
      }),

    /**
     * Start initialized scraper job with validated email
     */
    start: (jobId: string, email: string) =>
      request<{ job_id: string; status: string }>('/api/scraper/start/' + jobId, {
        method: 'POST',
        body: JSON.stringify({ email }),
      }),

    /**
     * Trigger new scraper pipeline run (Direct)
     */
    run: (params: { category: string; country?: string; count?: number; steps?: string }) =>
      request<{ job_id: string; status: string }>('/api/scraper/run', {
        method: 'POST',
        body: JSON.stringify(params),
      }),

    /**
     * Get status of scraper job
     */
    getStatus: (jobId: string) => request<any>(`/api/scraper/status/${jobId}`),

    /**
     * Resume existing scraper pipeline run
     */
    resume: (params: { run_id: string; steps?: string }) =>
      request<{ job_id: string; status: string }>('/api/scraper/resume', {
        method: 'POST',
        body: JSON.stringify(params),
      }),
  },

  health: {
    /**
     * Check API health
     */
    check: () => request<{ status: string; service: string; version: string }>('/api/health'),
  },
};
