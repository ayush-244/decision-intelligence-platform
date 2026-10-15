import { apiFetch } from '@/services/api/client';

import type { HealthResponse, VersionResponse } from '@/features/system/types';

export function getHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>('/api/v1/health');
}

export function getVersion(): Promise<VersionResponse> {
  return apiFetch<VersionResponse>('/api/v1/version');
}
