export interface Citation {
  resource_type: string;
  resource_id: string;
  label: string;
  excerpt: string;
}

export interface CopilotMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  citations: Citation[];
  created_at: string;
}

export interface CopilotConversation {
  id: string;
  title: string;
  dataset_id: string | null;
  session_id: string | null;
  messages: CopilotMessage[];
  pinned_insights: string[];
  suggested_questions: string[];
  context_summary: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface CreateConversationRequest {
  title?: string;
  dataset_id?: string;
  session_id?: string;
}

export interface SendMessageRequest {
  content: string;
}

export interface CopilotContext {
  dataset: Record<string, unknown>;
  data_quality: Record<string, unknown>;
  statistics: Record<string, unknown>[];
  causal: Record<string, unknown>[];
  simulations: Record<string, unknown>[];
  decisions: Record<string, unknown>[];
  reports: Record<string, unknown>[];
  session: Record<string, unknown> | null;
  prompt_preview: string;
}
