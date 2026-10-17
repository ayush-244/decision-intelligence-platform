import { apiFetchData } from '@/services/api/client';

import type { CausalAnalysisRun, CausalAnalyzeRequest, DAGVersion } from '@/features/causal/types';

export async function runCausalAnalysis(body: CausalAnalyzeRequest): Promise<CausalAnalysisRun> {
  return apiFetchData<CausalAnalysisRun>('/api/v1/causal/analyze', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function fetchCausalAnalysis(analysisId: string): Promise<CausalAnalysisRun> {
  return apiFetchData<CausalAnalysisRun>(`/api/v1/causal/${analysisId}`);
}

export async function fetchCausalHistory(datasetId: string): Promise<CausalAnalysisRun[]> {
  return apiFetchData<CausalAnalysisRun[]>(`/api/v1/causal/history?dataset_id=${datasetId}`);
}

export async function createDAG(body: {
  dataset_id: string;
  name: string;
  nodes: { id: string; label: string; role?: string; position?: { x: number; y: number } }[];
  edges: { source: string; target: string }[];
  variable_roles: Record<string, string>;
}): Promise<DAGVersion> {
  return apiFetchData<DAGVersion>('/api/v1/causal/dag', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function fetchDAG(dagId: string): Promise<DAGVersion> {
  return apiFetchData<DAGVersion>(`/api/v1/causal/dag/${dagId}`);
}
