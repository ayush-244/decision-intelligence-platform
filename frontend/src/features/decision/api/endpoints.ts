import { apiFetchData } from '@/services/api/client';

import type { DecisionObjective, DecisionRun, RunDecisionRequest } from '@/features/decision/types';

export async function runDecisionAnalysis(body: RunDecisionRequest): Promise<DecisionRun> {
  return apiFetchData<DecisionRun>('/api/v1/decisions/analyze', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function fetchDecision(decisionId: string): Promise<DecisionRun> {
  return apiFetchData<DecisionRun>(`/api/v1/decisions/${decisionId}`);
}

export async function fetchDecisionHistory(datasetId: string): Promise<DecisionRun[]> {
  return apiFetchData<DecisionRun[]>(`/api/v1/decisions?dataset_id=${datasetId}`);
}

export async function fetchRecommendations(decisionId: string): Promise<unknown[]> {
  return apiFetchData(`/api/v1/recommendations?decision_id=${decisionId}`);
}

export async function fetchTradeoffs(decisionId: string): Promise<unknown[]> {
  return apiFetchData(`/api/v1/tradeoffs?decision_id=${decisionId}`);
}

export async function fetchPriorities(decisionId: string): Promise<unknown[]> {
  return apiFetchData(`/api/v1/priorities?decision_id=${decisionId}`);
}

export async function fetchObjectives(): Promise<DecisionObjective[]> {
  return apiFetchData<DecisionObjective[]>('/api/v1/objectives');
}

export async function fetchSimulationHistoryForDecision(
  datasetId: string,
): Promise<Array<{ id: string; name: string; status: string }>> {
  return apiFetchData(`/api/v1/simulations/history?dataset_id=${datasetId}`);
}
