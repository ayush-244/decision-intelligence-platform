import { getAccessToken, getActiveOrganizationId } from '@/features/auth/session';
import type {
  Dataset,
  DatasetPreview,
  DatasetVersion,
  UploadResult,
} from '@/features/datasets/types';
import { apiFetch, apiFetchData } from '@/services/api/client';
import { env } from '@/config/env';

function orgHeaders(): Record<string, string> {
  const organizationId = getActiveOrganizationId();
  if (!organizationId) {
    throw new Error('No active organization selected.');
  }
  return { 'X-Organization-ID': organizationId };
}

async function uploadMultipart(path: string, formData: FormData): Promise<UploadResult> {
  const token = getAccessToken();
  const response = await fetch(`${env.apiBaseUrl}${path}`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      ...orgHeaders(),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: formData,
  });
  if (!response.ok) {
    const body = (await response.json()) as { error?: { message?: string } };
    throw new Error(body.error?.message ?? 'Upload failed.');
  }
  const envelope = (await response.json()) as { data: UploadResult };
  return envelope.data;
}

export function fetchDatasets(projectId: string): Promise<Dataset[]> {
  return apiFetchData<Dataset[]>(`/api/v1/datasets?project_id=${projectId}`, {
    headers: orgHeaders(),
  });
}

export function fetchDataset(datasetId: string): Promise<Dataset> {
  return apiFetchData<Dataset>(`/api/v1/datasets/${datasetId}`, { headers: orgHeaders() });
}

export function fetchDatasetVersions(datasetId: string): Promise<DatasetVersion[]> {
  return apiFetchData<DatasetVersion[]>(`/api/v1/datasets/${datasetId}/versions`, {
    headers: orgHeaders(),
  });
}

export function fetchDatasetPreview(
  datasetId: string,
  versionId?: string,
): Promise<DatasetPreview> {
  const query = versionId ? `?version_id=${versionId}` : '';
  return apiFetchData<DatasetPreview>(`/api/v1/datasets/${datasetId}/preview${query}`, {
    headers: orgHeaders(),
  });
}

export function uploadDataset(
  projectId: string,
  file: File,
  name?: string,
  description?: string,
): Promise<UploadResult> {
  const form = new FormData();
  form.append('project_id', projectId);
  form.append('file', file);
  if (name) form.append('name', name);
  if (description) form.append('description', description);
  return uploadMultipart('/api/v1/datasets/upload', form);
}

export function uploadDatasetVersion(datasetId: string, file: File): Promise<UploadResult> {
  const form = new FormData();
  form.append('file', file);
  return uploadMultipart(`/api/v1/datasets/${datasetId}/new-version`, form);
}

export async function deleteDataset(datasetId: string): Promise<void> {
  await apiFetch(`/api/v1/datasets/${datasetId}`, {
    method: 'DELETE',
    headers: orgHeaders(),
  });
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
