import { apiFetchData } from '@/services/api/client';

import type {
  AnalysisHistoryItem,
  AnalysisRun,
  AnalyzeRequest,
  TestRecommendation,
  VariableSpec,
  AnalysisGoal,
} from '@/features/statistics/types';

export async function runStatisticalAnalysis(body: AnalyzeRequest): Promise<AnalysisRun> {
  return apiFetchData<AnalysisRun>('/api/v1/statistics/analyze', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function fetchAnalysis(analysisId: string): Promise<AnalysisRun> {
  return apiFetchData<AnalysisRun>(`/api/v1/statistics/${analysisId}`);
}

export async function fetchAnalysisHistory(
  datasetId: string,
  versionId?: string,
): Promise<AnalysisHistoryItem[]> {
  const params = new URLSearchParams({ dataset_id: datasetId });
  if (versionId) params.set('version_id', versionId);
  return apiFetchData<AnalysisHistoryItem[]>(`/api/v1/statistics/history?${params}`);
}

export async function fetchRecommendations(
  datasetId: string,
  goal: AnalysisGoal,
  variables: VariableSpec[],
  versionId?: string,
): Promise<TestRecommendation> {
  return apiFetchData<TestRecommendation>('/api/v1/statistics/recommendations', {
    method: 'POST',
    body: JSON.stringify({
      dataset_id: datasetId,
      version_id: versionId,
      goal,
      variables,
    }),
  });
}
