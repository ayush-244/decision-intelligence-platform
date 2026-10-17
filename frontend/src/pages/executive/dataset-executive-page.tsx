import { useMemo, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft,
  Download,
  FileText,
  Loader2,
  Presentation,
  Sparkles,
  TrendingUp,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  useDecisionsForReportQuery,
  useExecutiveDashboardQuery,
  useExecutiveReportHistoryQuery,
  useExecutiveReportQuery,
  useExportReportMutation,
  useGenerateReportMutation,
  type ExecutiveReport,
  type TimelineItem,
} from '@/features/executive';
import { cn } from '@/lib/utils';

/** Safe display of loosely-typed narrative fields from the API. */
function asText(value: unknown, fallback: string): string {
  if (typeof value === 'string' && value.length > 0) return value;
  if (typeof value === 'number') return String(value);
  return fallback;
}

function HealthBadge({ score }: { score: number }) {
  const label = score >= 0.75 ? 'Strong' : score >= 0.5 ? 'Stable' : 'Needs attention';
  const tone =
    score >= 0.75
      ? 'bg-emerald-100 text-emerald-800'
      : score >= 0.5
        ? 'bg-sky-100 text-sky-800'
        : 'bg-amber-100 text-amber-800';
  return (
    <span className={cn('rounded-full px-3 py-1 text-sm font-medium', tone)}>
      {label} · {(score * 100).toFixed(0)}%
    </span>
  );
}

function DashboardPanel({ datasetId }: { datasetId: string }) {
  const { data, isLoading } = useExecutiveDashboardQuery(datasetId);
  if (isLoading || !data) {
    return (
      <div className="text-muted-foreground flex items-center gap-2">
        <Loader2 className="size-4 animate-spin" />
        Loading executive dashboard…
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <Card>
        <CardHeader className="pb-2">
          <CardDescription>Business health</CardDescription>
          <CardTitle className="flex items-center justify-between text-lg">
            Health
            <HealthBadge score={data.business_health_score} />
          </CardTitle>
        </CardHeader>
        <CardContent className="text-muted-foreground text-sm">
          Composite of decision completion and recommendation confidence.
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardDescription>Decision pipeline</CardDescription>
          <CardTitle className="text-2xl">{data.decision_pipeline.completed}</CardTitle>
        </CardHeader>
        <CardContent className="text-muted-foreground text-sm">
          {data.decision_pipeline.completed} completed · {data.decision_pipeline.total} total
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardDescription>ROI overview</CardDescription>
          <CardTitle className="text-2xl">
            {((data.roi_overview.average ?? 0) * 100).toFixed(0)}%
          </CardTitle>
        </CardHeader>
        <CardContent className="text-muted-foreground text-sm">
          Peak {((data.roi_overview.max ?? 0) * 100).toFixed(0)}% across scenarios
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardDescription>Reports generated</CardDescription>
          <CardTitle className="text-2xl">{data.historical_reports}</CardTitle>
        </CardHeader>
        <CardContent className="text-muted-foreground text-sm">
          Versioned executive intelligence artifacts
        </CardContent>
      </Card>
    </div>
  );
}

function TimelinePanel({ items }: { items: TimelineItem[] }) {
  if (items.length === 0) {
    return <p className="text-muted-foreground text-sm">No implementation roadmap yet.</p>;
  }
  return (
    <div className="space-y-4">
      {items.map((item) => (
        <div key={item.priority} className="border-primary/30 relative border-l-2 pl-6">
          <div className="bg-primary absolute top-1 -left-2 size-3 rounded-full" />
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h4 className="font-medium">
              P{item.priority}: {item.title}
            </h4>
            <span className="text-muted-foreground text-xs">{item.timeline}</span>
          </div>
          <p className="text-muted-foreground mt-1 text-sm">{item.impact}</p>
          <div className="mt-2 flex flex-wrap gap-2 text-xs">
            <span className="bg-muted rounded px-2 py-0.5">Effort: {item.effort}</span>
            <span className="bg-muted rounded px-2 py-0.5">Risk: {item.risk_level}</span>
            <span className="bg-muted rounded px-2 py-0.5">Owner: {item.business_owner}</span>
          </div>
          <ul className="text-muted-foreground mt-2 list-inside list-disc text-xs">
            {item.milestones.map((m) => (
              <li key={m}>{m}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

function ReportViewer({ report }: { report: ExecutiveReport }) {
  const result = report.result;
  const exportMutation = useExportReportMutation();

  return (
    <div className="space-y-6">
      <Card className="border-primary/20 from-primary/5 bg-gradient-to-br to-transparent">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="text-primary size-5" />
            Executive summary
          </CardTitle>
        </CardHeader>
        <CardContent className="text-base leading-relaxed">{result.executive_summary}</CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Confidence</CardDescription>
            <CardTitle className="capitalize">{result.confidence_assessment?.level}</CardTitle>
          </CardHeader>
          <CardContent className="text-sm">{result.confidence_assessment?.summary}</CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Expected ROI</CardDescription>
            <CardTitle>
              <TrendingUp className="mr-1 inline size-4" />
              {asText(result.expected_roi?.narrative, '—').slice(0, 80)}…
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Risk</CardDescription>
            <CardTitle className="text-sm font-normal">
              {asText(result.expected_risks?.summary, 'Review risk tolerance.')}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Key findings</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="list-inside list-disc space-y-2 text-sm">
            {(result.key_findings ?? []).map((f, i) => (
              <li key={i}>{f}</li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Decision narrative</CardTitle>
          <CardDescription>What happened, why, and what to do next</CardDescription>
        </CardHeader>
        <CardContent className="text-sm leading-relaxed whitespace-pre-wrap">
          {result.narrative}
        </CardContent>
      </Card>

      {(result.explainability ?? []).map((block) => (
        <Card key={block.recommendation_title}>
          <CardHeader>
            <CardTitle className="text-base">{block.recommendation_title}</CardTitle>
            <CardDescription>{block.why}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <p>{block.business_interpretation}</p>
            <details className="rounded border p-3">
              <summary className="cursor-pointer font-medium">Evidence chain</summary>
              <div className="text-muted-foreground mt-3 space-y-2">
                {block.evidence.statistical && <p>Statistical: {block.evidence.statistical}</p>}
                <p>Causal: {block.evidence.causal}</p>
                <p>Simulation: {block.evidence.simulation}</p>
                <p>Decision: {block.evidence.decision}</p>
              </div>
            </details>
            <div>
              <p className="font-medium">Alternatives</p>
              <ul className="text-muted-foreground list-inside list-disc">
                {block.alternative_actions.map((a) => (
                  <li key={a}>{a}</li>
                ))}
              </ul>
            </div>
          </CardContent>
        </Card>
      ))}

      <Card>
        <CardHeader>
          <CardTitle>Implementation roadmap</CardTitle>
        </CardHeader>
        <CardContent>
          <TimelinePanel items={result.implementation_roadmap ?? []} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="size-4" />
            Export center
          </CardTitle>
          <CardDescription>Markdown, CSV, JSON, and print-ready PDF summaries</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {(['markdown', 'csv', 'json', 'pdf'] as const).map((format) => (
            <Button
              key={format}
              variant="outline"
              size="sm"
              disabled={exportMutation.isPending}
              onClick={() => exportMutation.mutate({ reportId: report.id, format })}
            >
              <FileText className="mr-1 size-3" />
              {format.toUpperCase()}
            </Button>
          ))}
          <Button variant="outline" size="sm" disabled>
            <Presentation className="mr-1 size-3" />
            PowerPoint-ready (MD)
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

export function DatasetExecutivePage() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const [searchParams] = useSearchParams();
  const projectId = searchParams.get('project_id') ?? '';
  const [selectedReportId, setSelectedReportId] = useState<string | undefined>();
  const [reportName, setReportName] = useState('Executive Intelligence Brief');
  const [objective, setObjective] = useState(
    'Drive measurable business outcomes from causal evidence',
  );
  const [decisionRunId, setDecisionRunId] = useState('');
  const [activePanel, setActivePanel] = useState<'generate' | 'history' | 'viewer'>('generate');

  const history = useExecutiveReportHistoryQuery(datasetId);
  const decisions = useDecisionsForReportQuery(datasetId);
  const report = useExecutiveReportQuery(selectedReportId);
  const generate = useGenerateReportMutation(datasetId);

  const completedDecisions = useMemo(
    () => (decisions.data ?? []).filter((d) => d.status === 'completed'),
    [decisions.data],
  );

  async function handleGenerate() {
    if (!datasetId || !decisionRunId) return;
    const result = await generate.mutateAsync({
      dataset_id: datasetId,
      decision_run_id: decisionRunId,
      name: reportName,
      business_objective: objective,
      include_technical_appendix: false,
    });
    setSelectedReportId(result.id);
    setActivePanel('viewer');
  }

  return (
    <div className="mx-auto max-w-6xl space-y-8 p-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <Button asChild variant="ghost" size="sm" className="mb-2 -ml-2">
            <Link to={`/app/datasets/${datasetId}?project_id=${projectId}`}>
              <ArrowLeft className="mr-1 size-4" />
              Back to dataset
            </Link>
          </Button>
          <h1 className="text-display text-2xl sm:text-[1.75rem]">Executive Intelligence</h1>
          <p className="text-muted-foreground">
            Business-ready reports from your decision pipeline — no statistical jargon required.
          </p>
        </div>
      </div>

      {datasetId && <DashboardPanel datasetId={datasetId} />}

      <div className="flex flex-wrap gap-2 border-b pb-4">
        {(
          [
            ['generate', 'Generate report'],
            ['history', 'Report history'],
            ['viewer', 'Report viewer'],
          ] as const
        ).map(([id, label]) => (
          <Button
            key={id}
            variant={activePanel === id ? 'default' : 'outline'}
            size="sm"
            disabled={id === 'viewer' && !selectedReportId}
            onClick={() => setActivePanel(id)}
          >
            {label}
          </Button>
        ))}
      </div>

      {activePanel === 'generate' && (
        <Card>
          <CardHeader>
            <CardTitle>Create executive report</CardTitle>
            <CardDescription>
              Select a completed decision analysis to transform into leadership-ready intelligence.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Report name</label>
              <Input value={reportName} onChange={(e) => setReportName(e.target.value)} />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Decision analysis</label>
              <select
                className="border-input bg-background flex h-10 w-full rounded-md border px-3 text-sm"
                value={decisionRunId}
                onChange={(e) => setDecisionRunId(e.target.value)}
              >
                <option value="">Select completed decision…</option>
                {completedDecisions.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2 sm:col-span-2">
              <label className="text-sm font-medium">Business objective</label>
              <Input value={objective} onChange={(e) => setObjective(e.target.value)} />
            </div>
            <Button
              className="sm:col-span-2"
              disabled={!decisionRunId || generate.isPending}
              onClick={() => void handleGenerate()}
            >
              {generate.isPending ? (
                <Loader2 className="mr-2 size-4 animate-spin" />
              ) : (
                <Sparkles className="mr-2 size-4" />
              )}
              Generate executive report
            </Button>
          </CardContent>
        </Card>
      )}

      {activePanel === 'history' && (
        <Card>
          <CardHeader>
            <CardTitle>Report history</CardTitle>
            <CardDescription>
              Versioned executive artifacts linked to decision analyses
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {(history.data ?? []).length === 0 && (
              <p className="text-muted-foreground text-sm">
                No reports yet. Generate your first brief.
              </p>
            )}
            {(history.data ?? []).map((item) => (
              <button
                key={item.id}
                type="button"
                className="hover:bg-muted/50 flex w-full items-center justify-between rounded-lg border p-3 text-left"
                onClick={() => {
                  setSelectedReportId(item.id);
                  setActivePanel('viewer');
                }}
              >
                <div>
                  <p className="font-medium">{item.name}</p>
                  <p className="text-muted-foreground text-xs">
                    v{item.version_number} · {new Date(item.created_at).toLocaleString()}
                  </p>
                </div>
                <span className="bg-muted rounded-full px-2 py-0.5 text-xs capitalize">
                  {item.status}
                </span>
              </button>
            ))}
          </CardContent>
        </Card>
      )}

      {activePanel === 'viewer' && (
        <>
          {report.isLoading && (
            <div className="text-muted-foreground flex items-center gap-2">
              <Loader2 className="size-4 animate-spin" />
              Loading report…
            </div>
          )}
          {report.data && <ReportViewer report={report.data} />}
        </>
      )}
    </div>
  );
}
