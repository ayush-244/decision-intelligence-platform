import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  BookOpen,
  Download,
  Loader2,
  MessageSquare,
  PanelRight,
  Pin,
  Send,
  Sparkles,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { useDatasetQuery } from '@/features/datasets';
import {
  useCopilotContextQuery,
  useCopilotConversationQuery,
  useCopilotConversationsQuery,
  useCreateConversationMutation,
  useSendMessageMutation,
  sendMessage as sendMessageApi,
  type Citation,
  type CopilotMessage,
} from '@/features/copilot';
import { cn } from '@/lib/utils';

function MessageBubble({ message }: { message: CopilotMessage }) {
  const isUser = message.role === 'user';
  return (
    <div className={cn('flex flex-col gap-2', isUser ? 'items-end' : 'items-start')}>
      <div
        className={cn(
          'max-w-[85%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap',
          isUser ? 'bg-primary text-primary-foreground' : 'bg-muted',
        )}
      >
        {message.content}
      </div>
      {!isUser && message.citations.length > 0 ? (
        <div className="flex max-w-[85%] flex-wrap gap-1">
          {message.citations.map((c) => (
            <span
              key={`${c.resource_type}-${c.resource_id}`}
              className="bg-primary/10 text-primary rounded-full px-2 py-0.5 text-xs"
            >
              {c.label}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function EvidencePanel({ citations }: { citations: Citation[] }) {
  if (citations.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        Citations from assistant responses appear here with links to verified analyses.
      </p>
    );
  }
  return (
    <ul className="space-y-3">
      {citations.map((c) => (
        <li key={`${c.resource_type}-${c.resource_id}`} className="rounded-lg border p-3 text-sm">
          <p className="font-medium">{c.label}</p>
          <p className="text-muted-foreground mt-1 text-xs">{c.resource_type}</p>
          {c.excerpt ? <p className="mt-2 text-xs">{c.excerpt}</p> : null}
        </li>
      ))}
    </ul>
  );
}

export function CopilotWorkspacePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const datasetId = searchParams.get('datasetId') ?? '';
  const sessionId = searchParams.get('sessionId') ?? undefined;
  const conversationId = searchParams.get('conversationId') ?? '';

  const [draft, setDraft] = useState('');
  const [showContext, setShowContext] = useState(true);
  const [showEvidence, setShowEvidence] = useState(true);

  const dataset = useDatasetQuery(datasetId || undefined);
  const conversations = useCopilotConversationsQuery(datasetId || undefined);
  const conversation = useCopilotConversationQuery(conversationId);
  const context = useCopilotContextQuery(datasetId, sessionId);
  const createConversation = useCreateConversationMutation();
  const sendMessage = useSendMessageMutation(conversationId);

  useEffect(() => {
    const first = conversations.data?.[0];
    if (!datasetId && first?.dataset_id) {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.set('datasetId', first.dataset_id!);
        return next;
      });
    }
  }, [conversations.data, datasetId, setSearchParams]);

  const buildCreateRequest = (title: string) =>
    sessionId
      ? { title, dataset_id: datasetId, session_id: sessionId }
      : { title, dataset_id: datasetId };

  const active = conversation.data;
  const allCitations = useMemo(
    () =>
      (active?.messages ?? [])
        .filter((m) => m.role === 'assistant')
        .flatMap((m) => m.citations),
    [active?.messages],
  );

  const handleNewConversation = async () => {
    if (!datasetId) return;
    const created = await createConversation.mutateAsync(buildCreateRequest('New conversation'));
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set('conversationId', created.id);
      return next;
    });
  };

  const handleSend = async () => {
    const text = draft.trim();
    if (!text || !datasetId) return;
    if (!conversationId) {
      const created = await createConversation.mutateAsync(buildCreateRequest(text.slice(0, 80)));
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.set('conversationId', created.id);
        return next;
      });
      await sendMessageApi(created.id, { content: text });
      setDraft('');
      return;
    }
    await sendMessage.mutateAsync({ content: text });
    setDraft('');
  };

  const handleExport = () => {
    if (!active) return;
    const blob = new Blob([JSON.stringify(active, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `delphi-copilot-${active.id}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  const suggested = active?.suggested_questions ?? [];

  return (
    <div className="mx-auto flex h-[calc(100vh-4rem)] w-full max-w-7xl flex-col gap-4 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 text-display text-2xl sm:text-[1.75rem]">
            <Sparkles className="text-primary size-5" />
            AI Decision Copilot
          </h2>
          <p className="text-muted-foreground text-sm">
            Business analyst on top of Delphi&apos;s verified analytical engine — never invents numbers.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" onClick={() => setShowContext((v) => !v)}>
            <BookOpen className="mr-1 size-3.5" />
            Context
          </Button>
          <Button variant="outline" size="sm" onClick={() => setShowEvidence((v) => !v)}>
            <PanelRight className="mr-1 size-3.5" />
            Evidence
          </Button>
          <Button variant="outline" size="sm" onClick={handleExport} disabled={!active}>
            <Download className="mr-1 size-3.5" />
            Export
          </Button>
        </div>
      </div>

      {!datasetId ? (
        <Card>
          <CardHeader>
            <CardTitle>Select a dataset</CardTitle>
            <CardDescription>
              Open the copilot from a dataset workspace or append{' '}
              <code className="text-xs">?datasetId=...</code> to the URL.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild variant="outline">
              <Link to="/app/datasets">Browse datasets</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-[240px_1fr_280px]">
          <Card className="flex min-h-0 flex-col">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Conversations</CardTitle>
              <CardDescription className="truncate text-xs">
                {dataset.data?.name ?? datasetId}
              </CardDescription>
            </CardHeader>
            <CardContent className="flex min-h-0 flex-1 flex-col gap-2">
              <Button
                size="sm"
                onClick={() => {
                  void handleNewConversation();
                }}
                disabled={createConversation.isPending}
              >
                New conversation
              </Button>
              <ul className="min-h-0 flex-1 space-y-1 overflow-y-auto">
                {(conversations.data ?? []).map((c) => (
                  <li key={c.id}>
                    <button
                      type="button"
                      onClick={() =>
                        setSearchParams((prev) => {
                          const next = new URLSearchParams(prev);
                          next.set('conversationId', c.id);
                          return next;
                        })
                      }
                      className={cn(
                        'hover:bg-muted/60 w-full rounded-md px-2 py-1.5 text-left text-sm',
                        c.id === conversationId && 'bg-primary/10 text-primary font-medium',
                      )}
                    >
                      <span className="line-clamp-2">{c.title}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card className="flex min-h-0 flex-col">
            <CardHeader className="border-b pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <MessageSquare className="size-4" />
                {active?.title ?? 'Start a conversation'}
              </CardTitle>
            </CardHeader>
            <CardContent className="flex min-h-0 flex-1 flex-col gap-3 pt-4">
              <div className="min-h-0 flex-1 space-y-4 overflow-y-auto pr-1">
                {(active?.messages ?? []).length === 0 ? (
                  <div className="text-muted-foreground space-y-3 text-sm">
                    <p>Ask about statistical results, causal assumptions, recommendations, or executive summaries.</p>
                    <div className="flex flex-wrap gap-2">
                      {suggested.map((q) => (
                        <button
                          key={q}
                          type="button"
                          className="hover:bg-muted rounded-full border px-3 py-1 text-xs"
                          onClick={() => setDraft(q)}
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  active?.messages.map((m) => <MessageBubble key={m.id} message={m} />)
                )}
                {sendMessage.isPending ? (
                  <div className="text-muted-foreground flex items-center gap-2 text-sm">
                    <Loader2 className="size-4 animate-spin" />
                    Analyzing verified context…
                  </div>
                ) : null}
              </div>
              <div className="flex gap-2">
                <Input
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  placeholder="Ask about recommendations, assumptions, or tradeoffs…"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      void handleSend();
                    }
                  }}
                />
                <Button
                  onClick={() => void handleSend()}
                  disabled={!draft.trim() || sendMessage.isPending || createConversation.isPending}
                >
                  <Send className="size-4" />
                </Button>
              </div>
            </CardContent>
          </Card>

          <div className="flex min-h-0 flex-col gap-4 overflow-y-auto">
            {showContext ? (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Context inspector</CardTitle>
                  <CardDescription className="text-xs">Structured verified outputs</CardDescription>
                </CardHeader>
                <CardContent className="space-y-2 text-xs">
                  <p>
                    Statistics: {context.data?.statistics.length ?? 0} · Causal:{' '}
                    {context.data?.causal.length ?? 0} · Simulations:{' '}
                    {context.data?.simulations.length ?? 0}
                  </p>
                  <pre className="bg-muted max-h-40 overflow-auto rounded-md p-2 whitespace-pre-wrap">
                    {context.data?.prompt_preview ?? 'Loading context…'}
                  </pre>
                </CardContent>
              </Card>
            ) : null}

            {showEvidence ? (
              <Card className="min-h-0 flex-1">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center gap-1 text-sm">
                    <Pin className="size-3.5" />
                    Evidence panel
                  </CardTitle>
                </CardHeader>
                <CardContent className="overflow-y-auto">
                  <EvidencePanel citations={allCitations} />
                </CardContent>
              </Card>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
