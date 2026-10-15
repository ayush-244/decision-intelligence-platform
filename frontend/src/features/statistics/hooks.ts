import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { getAccessToken } from '@/features/auth/session';
import {
  fetchAnalysis,
  fetchAnalysisHistory,
  fetchRecommendations,
  runStatisticalAnalysis,
} from '@/features/statistics/api/endpoints';
import type { AnalyzeRequest } from '@/features/statistics/types';

export const statisticsKeys = {
  analysis: (id: string) => ['statistics', 'analysis', id] as const,
  history: (datasetId: string, versionId?: string) =>
    ['statistics', 'history', datasetId, versionId ?? 'current'] as const,
  recommendations: (datasetId: string, goal: string) =>
    ['statistics', 'recommendations', datasetId, goal] as const,
};

export function useAnalysisQuery(analysisId: string | undefined) {
  return useQuery({
    queryKey: statisticsKeys.analysis(analysisId ?? 'none'),
    queryFn: () => fetchAnalysis(analysisId!),
    enabled: Boolean(analysisId && getAccessToken()),
  });
}

export function useAnalysisHistoryQuery(datasetId: string | undefined, versionId?: string) {
  return useQuery({
    queryKey: statisticsKeys.history(datasetId ?? 'none', versionId),
    queryFn: () => fetchAnalysisHistory(datasetId!, versionId),
    enabled: Boolean(datasetId && getAccessToken()),
  });
}

export function useRecommendationsMutation() {
  return useMutation({
    mutationFn: (vars: {
      datasetId: string;
      goal: AnalyzeRequest['goal'];
      variables: AnalyzeRequest['variables'];
      versionId?: string;
    }) => fetchRecommendations(vars.datasetId, vars.goal, vars.variables, vars.versionId),
  });
}

export function useRunAnalysisMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: AnalyzeRequest) => runStatisticalAnalysis(body),
    onSuccess: (result) => {
      toast.success('Statistical analysis complete', {
        description: result.result?.interpretation?.test_performed ?? result.test_type ?? 'Done',
      });
      void queryClient.invalidateQueries({
        queryKey: statisticsKeys.history(result.dataset_id),
      });
      void queryClient.setQueryData(statisticsKeys.analysis(result.id), result);
    },
    onError: (err: Error) => {
      toast.error(err.message || 'Analysis failed.');
    },
  });
}
