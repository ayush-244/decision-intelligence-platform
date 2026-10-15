import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import {
  createScenario,
  fetchCausalHistoryForSimulation,
  fetchScenarios,
  fetchSimulationHistory,
  runSimulation,
} from '@/features/simulation/api/endpoints';
import type { CreateScenarioRequest, RunSimulationRequest } from '@/features/simulation/types';
import { getAccessToken } from '@/features/auth/session';

export const simulationKeys = {
  history: (datasetId: string) => ['simulation', 'history', datasetId] as const,
  scenarios: (datasetId: string) => ['simulation', 'scenarios', datasetId] as const,
  causalModels: (datasetId: string) => ['simulation', 'causal-models', datasetId] as const,
};

export function useSimulationHistoryQuery(datasetId: string | undefined) {
  return useQuery({
    queryKey: simulationKeys.history(datasetId ?? ''),
    queryFn: () => fetchSimulationHistory(datasetId!),
    enabled: Boolean(datasetId && getAccessToken()),
  });
}

export function useScenariosQuery(datasetId: string | undefined) {
  return useQuery({
    queryKey: simulationKeys.scenarios(datasetId ?? ''),
    queryFn: () => fetchScenarios(datasetId!),
    enabled: Boolean(datasetId && getAccessToken()),
  });
}

export function useCausalModelsQuery(datasetId: string | undefined) {
  return useQuery({
    queryKey: simulationKeys.causalModels(datasetId ?? ''),
    queryFn: () => fetchCausalHistoryForSimulation(datasetId!),
    enabled: Boolean(datasetId && getAccessToken()),
  });
}

export function useRunSimulationMutation(datasetId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: RunSimulationRequest) => runSimulation(body),
    onSuccess: (result) => {
      if (datasetId) {
        void queryClient.invalidateQueries({ queryKey: simulationKeys.history(datasetId) });
      }
      toast.success('Simulation completed', {
        description: result.result?.interpretation?.business_interpretation?.slice(0, 80),
      });
    },
    onError: (error: Error) => {
      toast.error('Simulation failed', { description: error.message });
    },
  });
}

export function useCreateScenarioMutation(datasetId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateScenarioRequest) => createScenario(body),
    onSuccess: () => {
      if (datasetId) {
        void queryClient.invalidateQueries({ queryKey: simulationKeys.scenarios(datasetId) });
      }
      toast.success('Scenario saved');
    },
  });
}
