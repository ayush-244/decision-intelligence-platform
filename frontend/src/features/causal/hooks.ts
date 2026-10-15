import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { getAccessToken } from '@/features/auth/session';
import {
  createDAG,
  fetchCausalAnalysis,
  fetchCausalHistory,
  runCausalAnalysis,
} from '@/features/causal/api/endpoints';
import type { CausalAnalyzeRequest } from '@/features/causal/types';

export const causalKeys = {
  analysis: (id: string) => ['causal', 'analysis', id] as const,
  history: (datasetId: string) => ['causal', 'history', datasetId] as const,
};

export function useCausalAnalysisQuery(analysisId: string | undefined) {
  return useQuery({
    queryKey: causalKeys.analysis(analysisId ?? 'none'),
    queryFn: () => fetchCausalAnalysis(analysisId!),
    enabled: Boolean(analysisId && getAccessToken()),
  });
}

export function useCausalHistoryQuery(datasetId: string | undefined) {
  return useQuery({
    queryKey: causalKeys.history(datasetId ?? 'none'),
    queryFn: () => fetchCausalHistory(datasetId!),
    enabled: Boolean(datasetId && getAccessToken()),
  });
}

export function useRunCausalAnalysisMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CausalAnalyzeRequest) => runCausalAnalysis(body),
    onSuccess: (result) => {
      toast.success('Causal analysis complete', {
        description: result.result?.interpretation?.business_interpretation?.slice(0, 80) ?? 'Analysis finished',
      });
      void queryClient.invalidateQueries({ queryKey: causalKeys.history(result.dataset_id) });
    },
    onError: (err: Error) => toast.error(err.message || 'Causal analysis failed.'),
  });
}

export function useCreateDAGMutation() {
  return useMutation({
    mutationFn: createDAG,
    onError: (err: Error) => toast.error(err.message || 'Failed to save DAG.'),
  });
}
