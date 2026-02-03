/**
 * API client for backend communication.
 *
 * This module provides typed methods for all backend API endpoints.
 */

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

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

  imageAnalysis: {
    /**
     * Upload an image for visual analysis
     */
    upload: async (file: File, brand?: string, productName?: string) => {
      const formData = new FormData();
      formData.append('file', file);
      if (brand) formData.append('brand', brand);
      if (productName) formData.append('product_name', productName);

      const url = `${API_URL}/api/image-analysis/upload`;
      
      try {
        const response = await fetch(url, {
          method: 'POST',
          body: formData,
          // Note: Don't set Content-Type header - browser will set it with boundary
        });

        if (!response.ok) {
          const error = await response.json().catch(() => ({ error: 'Unknown error' }));
          throw new ApiError(response.status, error.error || response.statusText);
        }

        return response.json() as Promise<{ job_id: string; status: string; message: string }>;
      } catch (error) {
        if (error instanceof ApiError) throw error;
        throw new ApiError(0, 'Network error - could not connect to API server');
      }
    },

    /**
     * Get status of image analysis job
     */
    getStatus: (jobId: string) => request<any>(`/api/image-analysis/status/${jobId}`),

    /**
     * Get full analysis result for a completed job
     */
    getResult: (jobId: string) => request<any>(`/api/image-analysis/result/${jobId}`),

    /**
     * List all completed analyses
     */
    listAnalyses: () => request<{ analyses: any[] }>(`/api/image-analysis/list`),
  },

  rebrand: {
    /**
     * Start a rebrand job with two images
     */
    start: async (sourceFile: File, inspirationFile: File, brandIdentity: string) => {
      const formData = new FormData();
      formData.append('source_image', sourceFile);
      formData.append('inspiration_image', inspirationFile);
      formData.append('brand_identity', brandIdentity);

      const url = `${API_URL}/api/rebrand/start`;
      
      try {
        const response = await fetch(url, {
          method: 'POST',
          body: formData,
          // Note: Don't set Content-Type header - browser will set it with boundary
        });

        if (!response.ok) {
          const error = await response.json().catch(() => ({ error: 'Unknown error' }));
          throw new ApiError(response.status, error.error || response.statusText);
        }

        return response.json() as Promise<{ job_id: string; status: string; message: string }>;
      } catch (error) {
        if (error instanceof ApiError) throw error;
        throw new ApiError(0, 'Network error - could not connect to API server');
      }
    },

    /**
     * Get status of rebrand job
     */
    getStatus: (jobId: string) => request<any>(`/api/rebrand/status/${jobId}`),

    /**
     * Get full rebrand result for a completed job
     */
    getResult: (jobId: string) => request<any>(`/api/rebrand/result/${jobId}`),

    /**
     * List all completed rebrand jobs
     */
    list: () => request<{ jobs: any[] }>(`/api/rebrand/list`),
  },

  rebrandSession: {
    /**
     * Start a rebrand session for a category analysis
     * This will rebrand the user's product against all competitors
     */
    start: async (analysisId: string, sourceFile: File, brandIdentity: string, category: string) => {
      const formData = new FormData();
      formData.append('source_image', sourceFile);
      formData.append('brand_identity', brandIdentity);
      formData.append('category', category);

      const url = `${API_URL}/api/analysis/${analysisId}/rebrand-session/start`;
      
      try {
        const response = await fetch(url, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          const error = await response.json().catch(() => ({ error: 'Unknown error' }));
          throw new ApiError(response.status, error.error || response.statusText);
        }

        return response.json() as Promise<{ session_id: string; analysis_id: string; status: string; message: string }>;
      } catch (error) {
        if (error instanceof ApiError) throw error;
        throw new ApiError(0, 'Network error - could not connect to API server');
      }
    },

    /**
     * Get the rebrand session for a category analysis
     */
    getForAnalysis: (analysisId: string) => request<any>(`/api/analysis/${analysisId}/rebrand-session`),

    /**
     * Get status of a rebrand session
     */
    getStatus: (sessionId: string) => request<any>(`/api/rebrand-session/${sessionId}/status`),

    /**
     * Get full session result
     */
    getResult: (sessionId: string) => request<any>(`/api/rebrand-session/${sessionId}/result`),
  },
};
