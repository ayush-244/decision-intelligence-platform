import { apiFetch } from '@/services/api/client';

import type {
  CopilotContext,
  CopilotConversation,
  CreateConversationRequest,
  SendMessageRequest,
} from '@/features/copilot/types';

export function listConversations(params?: {
  dataset_id?: string;
  limit?: number;
}): Promise<CopilotConversation[]> {
  const search = new URLSearchParams();
  if (params?.dataset_id) search.set('dataset_id', params.dataset_id);
  if (params?.limit) search.set('limit', String(params.limit));
  const query = search.toString();
  return apiFetch<CopilotConversation[]>(`/api/v1/copilot/conversations${query ? `?${query}` : ''}`);
}

export function getConversation(conversationId: string): Promise<CopilotConversation> {
  return apiFetch<CopilotConversation>(`/api/v1/copilot/conversations/${conversationId}`);
}

export function createConversation(body: CreateConversationRequest): Promise<CopilotConversation> {
  return apiFetch<CopilotConversation>('/api/v1/copilot/conversations', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function sendMessage(
  conversationId: string,
  body: SendMessageRequest,
): Promise<CopilotConversation> {
  return apiFetch<CopilotConversation>(`/api/v1/copilot/conversations/${conversationId}/messages`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function getCopilotContext(params: {
  dataset_id: string;
  session_id?: string;
}): Promise<CopilotContext> {
  const search = new URLSearchParams({ dataset_id: params.dataset_id });
  if (params.session_id) search.set('session_id', params.session_id);
  return apiFetch<CopilotContext>(`/api/v1/copilot/context?${search.toString()}`);
}
