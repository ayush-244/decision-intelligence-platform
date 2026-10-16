import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  cancelJob,
  getCacheStats,
  getInfrastructureMetrics,
  getJob,
  getQueueStatus,
  listJobs,
  retryJob,
  submitJob,
} from '@/features/infrastructure/api/endpoints';
import type { SubmitJobRequest } from '@/features/infrastructure/types';

const infrastructureKeys = {
  all: ['infrastructure'] as const,
  jobs: () => [...infrastructureKeys.all, 'jobs'] as const,
  job: (id: string) => [...infrastructureKeys.all, 'job', id] as const,
  metrics: () => [...infrastructureKeys.all, 'metrics'] as const,
  cache: () => [...infrastructureKeys.all, 'cache'] as const,
  queue: () => [...infrastructureKeys.all, 'queue'] as const,
};

export function useJobsQuery(status?: string) {
  return useQuery({
    queryKey: [...infrastructureKeys.jobs(), status ?? 'all'],
    queryFn: () => listJobs(status ? { status } : undefined),
    refetchInterval: 5_000,
  });
}

export function useJobQuery(jobId: string) {
  return useQuery({
    queryKey: infrastructureKeys.job(jobId),
    queryFn: () => getJob(jobId),
    enabled: Boolean(jobId),
    refetchInterval: 3_000,
  });
}

export function useInfrastructureMetricsQuery() {
  return useQuery({
    queryKey: infrastructureKeys.metrics(),
    queryFn: getInfrastructureMetrics,
    refetchInterval: 10_000,
  });
}

export function useCacheStatsQuery() {
  return useQuery({
    queryKey: infrastructureKeys.cache(),
    queryFn: getCacheStats,
    refetchInterval: 15_000,
  });
}

export function useQueueStatusQuery() {
  return useQuery({
    queryKey: infrastructureKeys.queue(),
    queryFn: getQueueStatus,
    refetchInterval: 5_000,
  });
}

export function useSubmitJobMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: SubmitJobRequest) => submitJob(body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: infrastructureKeys.jobs() });
      void queryClient.invalidateQueries({ queryKey: infrastructureKeys.metrics() });
    },
  });
}

export function useCancelJobMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => cancelJob(jobId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: infrastructureKeys.jobs() });
    },
  });
}

export function useRetryJobMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => retryJob(jobId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: infrastructureKeys.jobs() });
    },
  });
}
