import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { getAccessToken } from '@/features/auth/session';
import {
  analyzeDatasetIntelligence,
  fetchDatasetIntelligence,
  fetchDatasetIntelligenceSummary,
} from '@/features/intelligence/api/endpoints';

export const intelligenceKeys = {
  report: (datasetId: string, versionId?: string) =>
    ['intelligence', 'report', datasetId, versionId ?? 'current'] as const,
  summary: (datasetId: string, versionId?: string) =>
    ['intelligence', 'summary', datasetId, versionId ?? 'current'] as const,
};

export function useDatasetIntelligenceQuery(datasetId: string | undefined, versionId?: string) {
  return useQuery({
    queryKey: intelligenceKeys.report(datasetId ?? 'none', versionId),
    queryFn: () => fetchDatasetIntelligence(datasetId!, versionId),
    enabled: Boolean(datasetId && getAccessToken()),
    retry: false,
  });
}

export function useDatasetIntelligenceSummaryQuery(
  datasetId: string | undefined,
  versionId?: string,
) {
  return useQuery({
    queryKey: intelligenceKeys.summary(datasetId ?? 'none', versionId),
    queryFn: () => fetchDatasetIntelligenceSummary(datasetId!, versionId),
    enabled: Boolean(datasetId && getAccessToken()),
    retry: false,
  });
}

export function useAnalyzeDatasetIntelligenceMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: { datasetId: string; versionId?: string }) =>
      analyzeDatasetIntelligence(vars.datasetId, vars.versionId),
    onSuccess: (result, vars) => {
      toast.success('Data intelligence analysis complete', {
        description: `Quality ${result.quality_score?.toFixed(0)} · Health ${result.health_score?.toFixed(0)}`,
      });
      void queryClient.invalidateQueries({
        queryKey: intelligenceKeys.report(vars.datasetId, vars.versionId),
      });
      void queryClient.invalidateQueries({
        queryKey: intelligenceKeys.summary(vars.datasetId, vars.versionId),
      });
    },
    onError: (err: Error) => {
      toast.error(err.message || 'Analysis failed.');
    },
  });
}
