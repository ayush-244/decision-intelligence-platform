import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import {
  addSessionComment,
  compareSessions,
  createDecisionSession,
  fetchDecisionSession,
  fetchDecisionSessions,
  fetchSessionTimeline,
  updateDecisionSession,
  workspaceSearch,
} from '@/features/workspace/api/endpoints';
import type { WorkflowStep, WorkspaceState } from '@/features/workspace/types';
import { getAccessToken } from '@/features/auth/session';

export const workspaceKeys = {
  sessions: (datasetId: string) => ['workspace', 'sessions', datasetId] as const,
  session: (sessionId: string) => ['workspace', 'session', sessionId] as const,
  timeline: (sessionId: string) => ['workspace', 'timeline', sessionId] as const,
  search: (q: string, datasetId?: string) => ['workspace', 'search', q, datasetId ?? ''] as const,
};

export function useDecisionSessionsQuery(datasetId: string | undefined) {
  return useQuery({
    queryKey: workspaceKeys.sessions(datasetId ?? ''),
    queryFn: () => fetchDecisionSessions(datasetId!),
    enabled: Boolean(datasetId && getAccessToken()),
  });
}

export function useDecisionSessionQuery(sessionId: string | undefined) {
  return useQuery({
    queryKey: workspaceKeys.session(sessionId ?? ''),
    queryFn: () => fetchDecisionSession(sessionId!),
    enabled: Boolean(sessionId && getAccessToken()),
  });
}

export function useSessionTimelineQuery(sessionId: string | undefined) {
  return useQuery({
    queryKey: workspaceKeys.timeline(sessionId ?? ''),
    queryFn: () => fetchSessionTimeline(sessionId!),
    enabled: Boolean(sessionId && getAccessToken()),
  });
}

export function useWorkspaceSearchQuery(query: string, datasetId?: string) {
  return useQuery({
    queryKey: workspaceKeys.search(query, datasetId),
    queryFn: () => workspaceSearch(query, datasetId),
    enabled: Boolean(query.length >= 2 && getAccessToken()),
  });
}

export function useCreateSessionMutation(datasetId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createDecisionSession,
    onSuccess: () => {
      if (datasetId) {
        void queryClient.invalidateQueries({ queryKey: workspaceKeys.sessions(datasetId) });
      }
      toast.success('Decision session created');
    },
  });
}

export function useUpdateSessionMutation(sessionId: string | undefined, datasetId?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: Parameters<typeof updateDecisionSession>[1]) =>
      updateDecisionSession(sessionId!, body),
    onSuccess: () => {
      if (sessionId) {
        void queryClient.invalidateQueries({ queryKey: workspaceKeys.session(sessionId) });
        void queryClient.invalidateQueries({ queryKey: workspaceKeys.timeline(sessionId) });
      }
      if (datasetId) {
        void queryClient.invalidateQueries({ queryKey: workspaceKeys.sessions(datasetId) });
      }
    },
  });
}

export function useCompareSessionsMutation() {
  return useMutation({
    mutationFn: ({ a, b }: { a: string; b: string }) => compareSessions(a, b),
  });
}

export function useSessionCommentMutation(sessionId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: string) => addSessionComment(sessionId!, body),
    onSuccess: () => {
      if (sessionId) {
        void queryClient.invalidateQueries({ queryKey: workspaceKeys.timeline(sessionId) });
      }
      toast.success('Comment added');
    },
  });
}

export function buildCanvasNodes(datasetId: string, projectId: string): WorkspaceState['canvas']['nodes'] {
  const q = `?project_id=${projectId}`;
  return [
    { id: 'intelligence', type: 'intelligence', title: 'Data intelligence', status: 'pending', href: `/app/datasets/${datasetId}/intelligence${q}` },
    { id: 'statistics', type: 'statistics', title: 'Statistical analysis', status: 'pending', href: `/app/datasets/${datasetId}/statistics${q}` },
    { id: 'causal', type: 'causal', title: 'Causal inference', status: 'pending', href: `/app/datasets/${datasetId}/causal${q}` },
    { id: 'simulation', type: 'simulation', title: 'Simulation', status: 'pending', href: `/app/datasets/${datasetId}/simulation${q}` },
    { id: 'decision', type: 'decision', title: 'Recommendations', status: 'pending', href: `/app/datasets/${datasetId}/decision${q}` },
    { id: 'executive', type: 'executive', title: 'Executive report', status: 'pending', href: `/app/datasets/${datasetId}/executive${q}` },
  ];
}

export function stepForNode(nodeId: string): WorkflowStep | undefined {
  const map: Record<string, WorkflowStep> = {
    intelligence: 'data_intelligence',
    statistics: 'statistical_analysis',
    causal: 'causal_analysis',
    simulation: 'simulation',
    decision: 'recommendations',
    executive: 'executive_report',
  };
  return map[nodeId];
}
