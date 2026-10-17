import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  createConversation,
  getConversation,
  getCopilotContext,
  listConversations,
  sendMessage,
} from '@/features/copilot/api/endpoints';
import type { CreateConversationRequest, SendMessageRequest } from '@/features/copilot/types';

const copilotKeys = {
  all: ['copilot'] as const,
  conversations: (datasetId?: string) =>
    [...copilotKeys.all, 'conversations', datasetId ?? 'all'] as const,
  conversation: (id: string) => [...copilotKeys.all, 'conversation', id] as const,
  context: (datasetId: string, sessionId?: string) =>
    [...copilotKeys.all, 'context', datasetId, sessionId ?? 'none'] as const,
};

export function useCopilotConversationsQuery(datasetId?: string) {
  return useQuery({
    queryKey: copilotKeys.conversations(datasetId),
    queryFn: () => listConversations(datasetId ? { dataset_id: datasetId } : undefined),
    enabled: Boolean(datasetId),
  });
}

export function useCopilotConversationQuery(conversationId: string) {
  return useQuery({
    queryKey: copilotKeys.conversation(conversationId),
    queryFn: () => getConversation(conversationId),
    enabled: Boolean(conversationId),
  });
}

export function useCopilotContextQuery(datasetId: string, sessionId?: string) {
  return useQuery({
    queryKey: copilotKeys.context(datasetId, sessionId),
    queryFn: () =>
      getCopilotContext(
        sessionId ? { dataset_id: datasetId, session_id: sessionId } : { dataset_id: datasetId },
      ),
    enabled: Boolean(datasetId),
  });
}

export function useCreateConversationMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateConversationRequest) => createConversation(body),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({
        queryKey: copilotKeys.conversations(data.dataset_id ?? undefined),
      });
    },
  });
}

export function useSendMessageMutation(conversationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: SendMessageRequest) => sendMessage(conversationId, body),
    onSuccess: (data) => {
      queryClient.setQueryData(copilotKeys.conversation(conversationId), data);
      void queryClient.invalidateQueries({
        queryKey: copilotKeys.conversations(data.dataset_id ?? undefined),
      });
    },
  });
}
