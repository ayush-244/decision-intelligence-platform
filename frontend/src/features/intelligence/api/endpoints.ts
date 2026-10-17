import { apiFetchData } from '@/services/api/client';

import type {
  IntelligenceAnalyzeResult,
  IntelligenceReport,
  IntelligenceSummary,
} from '@/features/intelligence/types';

export async function analyzeDatasetIntelligence(
  datasetId: string,
  versionId?: string,
): Promise<IntelligenceAnalyzeResult> {
  const query = versionId ? `?version_id=${versionId}` : '';
  return apiFetchData<IntelligenceAnalyzeResult>(
    `/api/v1/datasets/${datasetId}/intelligence/analyze${query}`,
    { method: 'POST' },
  );
}

export async function fetchDatasetIntelligence(
  datasetId: string,
  versionId?: string,
): Promise<IntelligenceReport> {
  const query = versionId ? `?version_id=${versionId}` : '';
  return apiFetchData<IntelligenceReport>(`/api/v1/datasets/${datasetId}/intelligence${query}`);
}

export async function fetchDatasetIntelligenceSummary(
  datasetId: string,
  versionId?: string,
): Promise<IntelligenceSummary> {
  const query = versionId ? `?version_id=${versionId}` : '';
  return apiFetchData<IntelligenceSummary>(`/api/v1/datasets/${datasetId}/summary${query}`);
}

export async function fetchDatasetQuality(datasetId: string, versionId?: string) {
  const query = versionId ? `?version_id=${versionId}` : '';
  return apiFetchData<Record<string, unknown>>(`/api/v1/datasets/${datasetId}/quality${query}`);
}

export async function fetchDatasetColumnsIntelligence(datasetId: string, versionId?: string) {
  const query = versionId ? `?version_id=${versionId}` : '';
  return apiFetchData<{ columns: unknown[] }>(`/api/v1/datasets/${datasetId}/columns${query}`);
}

export async function fetchDatasetCorrelations(datasetId: string, versionId?: string) {
  const query = versionId ? `?version_id=${versionId}` : '';
  return apiFetchData<Record<string, unknown>>(
    `/api/v1/datasets/${datasetId}/correlations${query}`,
  );
}

export async function fetchDatasetMissing(datasetId: string, versionId?: string) {
  const query = versionId ? `?version_id=${versionId}` : '';
  return apiFetchData<Record<string, unknown>>(`/api/v1/datasets/${datasetId}/missing${query}`);
}

export async function fetchDatasetOutliers(datasetId: string, versionId?: string) {
  const query = versionId ? `?version_id=${versionId}` : '';
  return apiFetchData<Record<string, unknown>>(`/api/v1/datasets/${datasetId}/outliers${query}`);
}
