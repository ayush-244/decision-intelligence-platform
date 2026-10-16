import { apiFetch } from '@/services/api/client';

import type {
  InfrastructureMetrics,
  JobSnapshot,
  SubmitJobRequest,
} from '@/features/infrastructure/types';

export function listJobs(params?: {
  status?: string;
  job_type?: string;
  limit?: number;
}): Promise<JobSnapshot[]> {
  const search = new URLSearchParams();
  if (params?.status) search.set('status', params.status);
  if (params?.job_type) search.set('job_type', params.job_type);
  if (params?.limit) search.set('limit', String(params.limit));
  const query = search.toString();
  return apiFetch<JobSnapshot[]>(`/api/v1/jobs${query ? `?${query}` : ''}`);
}

export function getJob(jobId: string): Promise<JobSnapshot> {
  return apiFetch<JobSnapshot>(`/api/v1/jobs/${jobId}`);
}

export function submitJob(body: SubmitJobRequest): Promise<JobSnapshot> {
  return apiFetch<JobSnapshot>('/api/v1/jobs', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function cancelJob(jobId: string): Promise<JobSnapshot> {
  return apiFetch<JobSnapshot>(`/api/v1/jobs/${jobId}/cancel`, { method: 'POST' });
}

export function retryJob(jobId: string): Promise<JobSnapshot> {
  return apiFetch<JobSnapshot>(`/api/v1/jobs/${jobId}/retry`, { method: 'POST' });
}

export function getInfrastructureMetrics(): Promise<InfrastructureMetrics> {
  return apiFetch<InfrastructureMetrics>('/api/v1/infrastructure/metrics');
}

export function getCacheStats(): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>('/api/v1/infrastructure/cache/stats');
}

export function getQueueStatus(): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>('/api/v1/infrastructure/queue');
}
