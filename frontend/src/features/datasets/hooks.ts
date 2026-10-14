import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  deleteDataset,
  fetchDataset,
  fetchDatasetPreview,
  fetchDatasets,
  fetchDatasetVersions,
  uploadDataset,
  uploadDatasetVersion,
} from '@/features/datasets/api/endpoints';
import { getAccessToken } from '@/features/auth/session';

export const datasetKeys = {
  list: (projectId: string) => ['datasets', 'list', projectId] as const,
  detail: (datasetId: string) => ['datasets', 'detail', datasetId] as const,
  versions: (datasetId: string) => ['datasets', 'versions', datasetId] as const,
  preview: (datasetId: string, versionId?: string) =>
    ['datasets', 'preview', datasetId, versionId ?? 'current'] as const,
};

export function useDatasetsQuery(projectId: string | undefined) {
  return useQuery({
    queryKey: datasetKeys.list(projectId ?? 'none'),
    queryFn: () => fetchDatasets(projectId!),
    enabled: Boolean(projectId && getAccessToken()),
  });
}

export function useDatasetQuery(datasetId: string | undefined) {
  return useQuery({
    queryKey: datasetKeys.detail(datasetId ?? 'none'),
    queryFn: () => fetchDataset(datasetId!),
    enabled: Boolean(datasetId && getAccessToken()),
  });
}

export function useDatasetVersionsQuery(datasetId: string | undefined) {
  return useQuery({
    queryKey: datasetKeys.versions(datasetId ?? 'none'),
    queryFn: () => fetchDatasetVersions(datasetId!),
    enabled: Boolean(datasetId && getAccessToken()),
  });
}

export function useDatasetPreviewQuery(datasetId: string | undefined, versionId?: string) {
  return useQuery({
    queryKey: datasetKeys.preview(datasetId ?? 'none', versionId),
    queryFn: () => fetchDatasetPreview(datasetId!, versionId),
    enabled: Boolean(datasetId && getAccessToken()),
  });
}

export function useUploadDatasetMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: { projectId: string; file: File; name?: string; description?: string }) =>
      uploadDataset(vars.projectId, vars.file, vars.name, vars.description),
    onSuccess: (_result, vars) => {
      void queryClient.invalidateQueries({ queryKey: datasetKeys.list(vars.projectId) });
    },
  });
}

export function useUploadDatasetVersionMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: { datasetId: string; file: File }) =>
      uploadDatasetVersion(vars.datasetId, vars.file),
    onSuccess: (_result, vars) => {
      void queryClient.invalidateQueries({ queryKey: datasetKeys.detail(vars.datasetId) });
      void queryClient.invalidateQueries({ queryKey: datasetKeys.versions(vars.datasetId) });
      void queryClient.invalidateQueries({ queryKey: datasetKeys.preview(vars.datasetId) });
    },
  });
}

export function useDeleteDatasetMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: { datasetId: string; projectId: string }) =>
      deleteDataset(vars.datasetId).then(() => vars),
    onSuccess: (vars) => {
      void queryClient.invalidateQueries({ queryKey: datasetKeys.list(vars.projectId) });
    },
  });
}
