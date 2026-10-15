import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import {
  fetchDecisionHistory,
  fetchObjectives,
  fetchSimulationHistoryForDecision,
  runDecisionAnalysis,
} from '@/features/decision/api/endpoints';
import type { RunDecisionRequest } from '@/features/decision/types';
import { getAccessToken } from '@/features/auth/session';

export const decisionKeys = {
  history: (datasetId: string) => ['decision', 'history', datasetId] as const,
  objectives: () => ['decision', 'objectives'] as const,
  simulations: (datasetId: string) => ['decision', 'simulations', datasetId] as const,
};

export function useDecisionHistoryQuery(datasetId: string | undefined) {
  return useQuery({
    queryKey: decisionKeys.history(datasetId ?? ''),
    queryFn: () => fetchDecisionHistory(datasetId!),
    enabled: Boolean(datasetId && getAccessToken()),
  });
}

export function useObjectivesQuery() {
  return useQuery({
    queryKey: decisionKeys.objectives(),
    queryFn: fetchObjectives,
    enabled: Boolean(getAccessToken()),
  });
}

export function useSimulationsForDecisionQuery(datasetId: string | undefined) {
  return useQuery({
    queryKey: decisionKeys.simulations(datasetId ?? ''),
    queryFn: () => fetchSimulationHistoryForDecision(datasetId!),
    enabled: Boolean(datasetId && getAccessToken()),
  });
}

export function useRunDecisionMutation(datasetId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: RunDecisionRequest) => runDecisionAnalysis(body),
    onSuccess: (result) => {
      if (datasetId) {
        void queryClient.invalidateQueries({ queryKey: decisionKeys.history(datasetId) });
      }
      toast.success('Decision analysis complete', {
        description: result.result?.overall_summary?.slice(0, 100),
      });
    },
    onError: (error: Error) => {
      toast.error('Decision analysis failed', { description: error.message });
    },
  });
}
