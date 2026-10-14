import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft,
  CheckCircle2,
  ChevronRight,
  Circle,
  GitCompare,
  Loader2,
  MessageSquare,
  PanelLeft,
  PanelRight,
  Pause,
  Play,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { useDatasetQuery } from '@/features/datasets';
import {
  WORKFLOW_STEPS,
  buildCanvasNodes,
  stepForNode,
  useCompareSessionsMutation,
  useCreateSessionMutation,
  useDecisionSessionQuery,
  useDecisionSessionsQuery,
  useSessionCommentMutation,
  useSessionTimelineQuery,
  useUpdateSessionMutation,
  type WorkflowStep,
} from '@/features/workspace';
import { cn } from '@/lib/utils';

/** Safe display of loosely-typed comparison values from the API. */
function formatComparisonValue(value: unknown): string {
  if (value == null) return '—';
  if (typeof value === 'string') return value;
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  return JSON.stringify(value);
}

function WorkflowRail({
  currentStep,
  percent,
  onSelect,
}: {
  currentStep: WorkflowStep;
  percent: number;
  onSelect: (step: WorkflowStep) => void;
}) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">Workflow progress</span>
        <span className="font-medium">{percent.toFixed(0)}%</span>
      </div>
      <div className="bg-muted h-1.5 overflow-hidden rounded-full">
        <div className="bg-primary h-full transition-all" style={{ width: `${percent}%` }} />
      </div>
      <ol className="space-y-1">
        {WORKFLOW_STEPS.map((step) => {
          const idx = WORKFLOW_STEPS.findIndex((s) => s.id === currentStep);
          const stepIdx = WORKFLOW_STEPS.findIndex((s) => s.id === step.id);
          const done = stepIdx <= idx;
          const active = step.id === currentStep;
          return (
            <li key={step.id}>
              <button
                type="button"
                onClick={() => onSelect(step.id)}
                className={cn(
                  'flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors',
                  active && 'bg-primary/10 text-primary font-medium',
                  !active && 'hover:bg-muted/60',
                )}
              >
                {done ? (
                  <CheckCircle2 className="size-3.5 shrink-0 text-emerald-600" />
                ) : (
                  <Circle className="text-muted-foreground size-3.5 shrink-0" />
                )}
                {step.label}
              </button>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

export function DecisionWorkspacePage() {
  const navigate = useNavigate();
  const { datasetId } = useParams<{ datasetId: string }>();
  const [searchParams] = useSearchParams();
  const projectId = searchParams.get('project_id') ?? '';
  const [sessionId, setSessionId] = useState<string | undefined>(
    searchParams.get('session_id') ?? undefined,
  );
  const [sessionName, setSessionName] = useState('Decision Session');
  const [comment, setComment] = useState('');
  const [compareId, setCompareId] = useState('');
  const [showSidebar, setShowSidebar] = useState(true);
  const [showTimeline, setShowTimeline] = useState(true);
  const [showContext] = useState(true);

  const dataset = useDatasetQuery(datasetId);
  const sessions = useDecisionSessionsQuery(datasetId);
  const session = useDecisionSessionQuery(sessionId);
  const timeline = useSessionTimelineQuery(sessionId);
  const createSession = useCreateSessionMutation(datasetId);
  const updateSession = useUpdateSessionMutation(sessionId, datasetId);
  const compare = useCompareSessionsMutation();
  const addComment = useSessionCommentMutation(sessionId);

  const progress = session.data?.progress;
  const canvasNodes = useMemo(
    () => session.data?.workspace_state?.canvas?.nodes ?? buildCanvasNodes(datasetId ?? '', projectId),
    [session.data, datasetId, projectId],
  );

  useEffect(() => {
    if (!sessionId && sessions.data?.[0]) {
      setSessionId(sessions.data[0].id);
    }
  }, [sessionId, sessions.data]);

  async function handleCreateSession() {
    if (!datasetId) return;
    const created = await createSession.mutateAsync({
      dataset_id: datasetId,
      name: sessionName,
    });
    setSessionId(created.id);
  }

  async function handleOpenNode(nodeId: string, href?: string) {
    const step = stepForNode(nodeId);
    if (sessionId && step) {
      await updateSession.mutateAsync({ current_step: step });
    }
    if (href) void navigate(href);
  }

  return (
    <div className="flex min-h-[calc(100dvh-8rem)] flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Button asChild variant="ghost" size="sm" className="-ml-2 mb-1">
            <Link to={`/app/datasets/${datasetId}?project_id=${projectId}`}>
              <ArrowLeft className="mr-1 size-4" />
              {dataset.data?.name ?? 'Dataset'}
            </Link>
          </Button>
          <h1 className="text-display text-xl">Decision Workspace</h1>
          <p className="text-muted-foreground text-sm">
            End-to-end analytical journey — intelligence through executive reporting.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="icon" onClick={() => setShowSidebar((v) => !v)} aria-label="Toggle sidebar">
            <PanelLeft className="size-4" />
          </Button>
          <Button variant="outline" size="icon" onClick={() => setShowTimeline((v) => !v)} aria-label="Toggle timeline">
            <PanelRight className="size-4" />
          </Button>
          {sessionId && (
            <>
              <Button
                variant="outline"
                size="sm"
                disabled={updateSession.isPending}
                onClick={() =>
                  void updateSession.mutateAsync({
                    action: session.data?.status === 'paused' ? 'resume' : 'pause',
                  })
                }
              >
                {session.data?.status === 'paused' ? (
                  <Play className="mr-1 size-3.5" />
                ) : (
                  <Pause className="mr-1 size-3.5" />
                )}
                {session.data?.status === 'paused' ? 'Resume' : 'Pause'}
              </Button>
              <Button
                size="sm"
                disabled={updateSession.isPending}
                onClick={() => void updateSession.mutateAsync({ action: 'complete' })}
              >
                Complete session
              </Button>
            </>
          )}
        </div>
      </div>

      <div className="grid flex-1 gap-4 lg:grid-cols-[240px_1fr_280px]">
        {showSidebar && (
          <aside className="space-y-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Sessions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {(sessions.data ?? []).map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => setSessionId(s.id)}
                    className={cn(
                      'w-full rounded-md border px-2 py-2 text-left text-sm',
                      sessionId === s.id && 'border-primary bg-primary/5',
                    )}
                  >
                    <p className="font-medium">{s.name}</p>
                    <p className="text-muted-foreground text-xs capitalize">{s.status}</p>
                  </button>
                ))}
                <div className="flex gap-2 pt-2">
                  <Input
                    value={sessionName}
                    onChange={(e) => setSessionName(e.target.value)}
                    placeholder="Session name"
                    className="h-8 text-xs"
                  />
                  <Button size="sm" disabled={createSession.isPending} onClick={() => void handleCreateSession()}>
                    New
                  </Button>
                </div>
              </CardContent>
            </Card>
            {progress && (
              <Card>
                <CardContent className="pt-4">
                  <WorkflowRail
                    currentStep={progress.current_step}
                    percent={progress.percent_complete}
                    onSelect={(step) => {
                      if (sessionId) void updateSession.mutateAsync({ current_step: step });
                    }}
                  />
                </CardContent>
              </Card>
            )}
          </aside>
        )}

        <main className="min-w-0 space-y-4">
          <Card className="border-dashed">
            <CardHeader>
              <CardTitle>Analysis canvas</CardTitle>
              <CardDescription>
                Open any module without leaving context. Your session preserves the journey.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {canvasNodes.map((node) => (
                  <button
                    key={node.id}
                    type="button"
                    onClick={() => void handleOpenNode(node.id, node.href)}
                    className="hover:border-primary/40 group rounded-lg border p-4 text-left transition-colors hover:bg-muted/30"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{node.title}</span>
                      <ChevronRight className="text-muted-foreground size-4 opacity-0 transition-opacity group-hover:opacity-100" />
                    </div>
                    <p className="text-muted-foreground mt-1 text-xs capitalize">{node.status}</p>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          {showContext && sessionId && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Comparison workspace</CardTitle>
                <CardDescription>Compare two decision sessions side by side</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex gap-2">
                  <select
                    className="border-input bg-background h-9 flex-1 rounded-md border px-2 text-sm"
                    value={compareId}
                    onChange={(e) => setCompareId(e.target.value)}
                  >
                    <option value="">Select session to compare…</option>
                    {(sessions.data ?? [])
                      .filter((s) => s.id !== sessionId)
                      .map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.name}
                        </option>
                      ))}
                  </select>
                  <Button
                    variant="outline"
                    disabled={!compareId || compare.isPending}
                    onClick={() => {
                      if (sessionId && compareId) {
                        void compare.mutateAsync({ a: sessionId, b: compareId });
                      }
                    }}
                  >
                    <GitCompare className="mr-1 size-3.5" />
                    Compare
                  </Button>
                </div>
                {compare.data && (
                  <div className="space-y-2 text-sm">
                    <p>{compare.data.summary}</p>
                    {compare.data.items.map((item) => (
                      <div
                        key={item.label}
                        className={cn(
                          'grid grid-cols-3 gap-2 rounded border p-2',
                          item.highlight && 'border-amber-300 bg-amber-50/50 dark:bg-amber-950/20',
                        )}
                      >
                        <span className="text-muted-foreground">{item.label}</span>
                        <span>{formatComparisonValue(item.value_a)}</span>
                        <span>{formatComparisonValue(item.value_b)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </main>

        {showTimeline && (
          <aside className="space-y-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Knowledge timeline</CardTitle>
              </CardHeader>
              <CardContent className="max-h-[420px] space-y-3 overflow-y-auto">
                {!sessionId && (
                  <p className="text-muted-foreground text-sm">Create or select a session to view activity.</p>
                )}
                {timeline.isLoading && (
                  <div className="text-muted-foreground flex items-center gap-2 text-sm">
                    <Loader2 className="size-4 animate-spin" />
                    Loading…
                  </div>
                )}
                {(timeline.data ?? []).map((event) => (
                  <div key={event.id} className="border-l-2 border-primary/30 pl-3">
                    <p className="text-sm font-medium">{event.title}</p>
                    {event.description && (
                      <p className="text-muted-foreground text-xs">{event.description}</p>
                    )}
                    <p className="text-muted-foreground mt-0.5 text-[10px]">
                      {new Date(event.occurred_at).toLocaleString()}
                    </p>
                  </div>
                ))}
              </CardContent>
            </Card>

            {sessionId && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center gap-1 text-sm">
                    <MessageSquare className="size-3.5" />
                    Comments
                  </CardTitle>
                  <CardDescription>Collaboration foundation — mentions ready</CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  <Input
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder="Add a note for your team…"
                    className="text-sm"
                  />
                  <Button
                    size="sm"
                    className="w-full"
                    disabled={!comment.trim() || addComment.isPending}
                    onClick={() => {
                      void addComment.mutateAsync(comment).then(() => setComment(''));
                    }}
                  >
                    Post comment
                  </Button>
                </CardContent>
              </Card>
            )}
          </aside>
        )}
      </div>
    </div>
  );
}
