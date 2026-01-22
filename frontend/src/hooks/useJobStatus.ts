import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../api/client';
import type { JobStatus } from '../types';

type UseJobStatusResult = {
  status: JobStatus | null;
  loading: boolean;
  error: string | null;
  isComplete: boolean;
  isFailed: boolean;
  refetch: () => void;
};

/**
 * Hook for polling job status.
 *
 * @param jobId - Job ID to poll
 * @param pollInterval - Polling interval in ms (default: 2000)
 */
export function useJobStatus(
  jobId: string | null,
  pollInterval: number = 2000
): UseJobStatusResult {
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<number | null>(null);

  const isComplete = status?.state === 'SUCCESS';
  const isFailed = status?.state === 'FAILURE';

  const fetchStatus = useCallback(async () => {
    if (!jobId) {
      setLoading(false);
      return;
    }

    try {
      const data = await api.scraper.getStatus(jobId);
      setStatus(data as JobStatus);
      setError(null);

      // Stop polling if complete or failed
      if (data.state === 'SUCCESS' || data.state === 'FAILURE') {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch job status');
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    if (!jobId) return;

    // Initial fetch
    fetchStatus();

    // Start polling
    intervalRef.current = window.setInterval(fetchStatus, pollInterval);

    // Cleanup
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [jobId, pollInterval, fetchStatus]);

  return { status, loading, error, isComplete, isFailed, refetch: fetchStatus };
}
