import { apiFetchData } from '@/services/api/client';

import type { DecisionSession, SearchResult, SessionComparison, SessionHistoryItem, TimelineEvent, WorkflowStep, WorkspaceState } from '@/features/workspace/types';

export async function createDecisionSession(body: {
  dataset_id: string;
  version_id?: string;
  name: string;
  description?: string;
}): Promise<SessionHistoryItem> {
  return apiFetchData<SessionHistoryItem>('/api/v1/sessions', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function fetchDecisionSessions(datasetId: string): Promise<SessionHistoryItem[]> {
  return apiFetchData<SessionHistoryItem[]>(`/api/v1/sessions?dataset_id=${datasetId}`);
}

export async function fetchDecisionSession(sessionId: string): Promise<DecisionSession> {
  return apiFetchData<DecisionSession>(`/api/v1/sessions/${sessionId}`);
}

export async function updateDecisionSession(
  sessionId: string,
  body: Partial<{
    name: string;
    current_step: WorkflowStep;
    workspace_state: WorkspaceState;
    action: 'pause' | 'resume' | 'complete';
  }>,
): Promise<SessionHistoryItem> {
  return apiFetchData<SessionHistoryItem>(`/api/v1/sessions/${sessionId}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
}

export async function fetchSessionTimeline(sessionId: string): Promise<TimelineEvent[]> {
  return apiFetchData<TimelineEvent[]>(`/api/v1/sessions/${sessionId}/timeline`);
}

export async function workspaceSearch(q: string, datasetId?: string): Promise<SearchResult[]> {
  const params = new URLSearchParams({ q });
  if (datasetId) params.set('dataset_id', datasetId);
  return apiFetchData<SearchResult[]>(`/api/v1/workspace/search?${params.toString()}`);
}

export async function compareSessions(
  sessionAId: string,
  sessionBId: string,
): Promise<SessionComparison> {
  return apiFetchData<SessionComparison>('/api/v1/workspace/compare', {
    method: 'POST',
    body: JSON.stringify({ session_a_id: sessionAId, session_b_id: sessionBId }),
  });
}

export async function fetchWorkspaceActivity(): Promise<unknown[]> {
  return apiFetchData<unknown[]>('/api/v1/workspace/activity');
}

export async function addSessionComment(sessionId: string, body: string): Promise<unknown> {
  return apiFetchData(`/api/v1/sessions/${sessionId}/comments`, {
    method: 'POST',
    body: JSON.stringify({ body, mentions: [] }),
  });
}
