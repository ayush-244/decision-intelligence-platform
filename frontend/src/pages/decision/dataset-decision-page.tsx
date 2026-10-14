import ReactECharts from 'echarts-for-react';
import { useMemo, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { Lightbulb, Loader2, Play } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  useDecisionHistoryQuery,
  useObjectivesQuery,
  useRunDecisionMutation,
  useSimulationsForDecisionQuery,
  type DecisionRun,
  type Recommendation,
} from '@/features/decision';
import { cn } from '@/lib/utils';

const STEPS = ['Goal', 'Simulations', 'Constraints', 'Recommendations'] as const;

function PriorityMatrix({ recommendations }: { recommendations: Recommendation[] }) {
  const option = useMemo(
    () => ({
      tooltip: {},
      xAxis: { name: 'Risk', min: 0, max: 1 },
      yAxis: { name: 'ROI (norm)', min: 0, max: 1 },
      series: [
        {
          type: 'scatter',
          symbolSize: 14,
          data: recommendations.map((r) => [
            r.risk,
            Math.min(1, (r.roi + 1) / 2),
            r.title,
          ]),
          label: { show: true, formatter: (p: { dataIndex: number }) => `#${p.dataIndex + 1}`, position: 'top' },
        },
      ],
    }),
    [recommendations],
  );
  return <ReactECharts option={option} theme="delphi" style={{ height: 280 }} />;
}

function ResultsPanel({ run }: { run: DecisionRun }) {
  const recs = run.result.recommendations ?? [];
  const tradeoffs = run.result.tradeoffs ?? [];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Executive summary</CardTitle>
        </CardHeader>
        <CardContent className="text-sm">{run.result.overall_summary}</CardContent>
      </Card>

      {recs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Priority matrix</CardTitle>
            <CardDescription>ROI vs risk — evidence-backed positioning</CardDescription>
          </CardHeader>
          <CardContent>
            <PriorityMatrix recommendations={recs} />
          </CardContent>
        </Card>
      )}

      <div className="space-y-4">
        {recs.map((rec) => (
          <Card key={rec.rank}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">
                  #{rec.rank} {rec.title}
                </CardTitle>
                <span
                  className={cn(
                    'rounded-full px-2 py-0.5 text-xs font-medium',
                    rec.status === 'approved' && 'bg-green-100 text-green-800',
                    rec.status === 'conditional' && 'bg-amber-100 text-amber-800',
                    rec.status === 'deferred' && 'bg-slate-100 text-slate-700',
                  )}
                >
                  {rec.status}
                </span>
              </div>
              <CardDescription>{rec.summary}</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <p className="text-muted-foreground">Score</p>
                <p className="font-semibold">{rec.decision_score.overall_score.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-muted-foreground">ROI</p>
                <p className="font-semibold">{(rec.roi * 100).toFixed(1)}%</p>
              </div>
              <div>
                <p className="text-muted-foreground">Risk</p>
                <p className="font-semibold">{(rec.risk * 100).toFixed(0)}%</p>
              </div>
              <div>
                <p className="text-muted-foreground">Confidence</p>
                <p className="font-semibold">{(rec.confidence * 100).toFixed(0)}%</p>
              </div>
              <p className="sm:col-span-2 lg:col-span-4">{rec.business_explanation}</p>
              <p className="text-xs text-muted-foreground sm:col-span-2 lg:col-span-4">
                Evidence: causal {rec.evidence.causal_analysis_id.slice(0, 8)}… → simulation{' '}
                {rec.evidence.simulation_run_id.slice(0, 8)}…
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {tradeoffs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Tradeoff explorer</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {tradeoffs.map((t, i) => (
              <div key={i} className="rounded-lg border p-3">
                <p className="font-medium">
                  {t.dimension_a} vs {t.dimension_b}
                </p>
                <p className="text-muted-foreground">{t.tradeoff_summary}</p>
                <p className="mt-1">{t.recommendation}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export function DatasetDecisionPage() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const [searchParams] = useSearchParams();
  const projectId = searchParams.get('project_id') ?? '';

  const [step, setStep] = useState(0);
  const [objective, setObjective] = useState('maximize_revenue');
  const [analysisName, setAnalysisName] = useState('Strategic decision analysis');
  const [selectedSims, setSelectedSims] = useState<string[]>([]);
  const [riskTolerance, setRiskTolerance] = useState('0.65');
  const [minConfidence, setMinConfidence] = useState('0.5');
  const [maxBudget, setMaxBudget] = useState('10000');
  const [lastRun, setLastRun] = useState<DecisionRun | null>(null);

  const { data: objectives } = useObjectivesQuery();
  const { data: simulations } = useSimulationsForDecisionQuery(datasetId);
  const { data: history } = useDecisionHistoryQuery(datasetId);
  const runMutation = useRunDecisionMutation(datasetId);

  const completedSims = (simulations ?? []).filter((s) => s.status === 'completed');

  const toggleSim = (id: string) => {
    setSelectedSims((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  };

  const handleRun = async () => {
    if (!datasetId) return;
    const ids = selectedSims.length ? selectedSims : completedSims.map((s) => s.id);
    if (!ids.length) return;
    const run = await runMutation.mutateAsync({
      dataset_id: datasetId,
      name: analysisName,
      primary_objective: objective,
      simulation_run_ids: ids,
      risk_tolerance: parseFloat(riskTolerance) || 0.65,
      min_confidence: parseFloat(minConfidence) || 0.5,
      ...(maxBudget ? { max_budget: parseFloat(maxBudget) } : {}),
    });
    setLastRun(run);
    setStep(3);
  };

  if (!datasetId) return null;

  return (
    <div className="mx-auto max-w-5xl space-y-8 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-display flex items-center gap-2 text-2xl sm:text-[1.75rem]">
            <Lightbulb className="size-6" />
            Decision Intelligence
          </h1>
          <p className="text-sm text-muted-foreground">
            Evidence-backed recommendations — not AI guesses
          </p>
        </div>
        <Button asChild variant="outline" size="sm">
          <Link to={`/app/datasets/${datasetId}?project_id=${projectId}`}>Back to dataset</Link>
        </Button>
      </div>

      <div className="flex flex-wrap gap-2">
        {STEPS.map((label, i) => (
          <button
            key={label}
            type="button"
            onClick={() => setStep(i)}
            className={cn(
              'rounded-full px-3 py-1 text-xs font-medium',
              step === i ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground',
            )}
          >
            {i + 1}. {label}
          </button>
        ))}
      </div>

      {step === 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Business goal</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium">Analysis name</label>
              <Input value={analysisName} onChange={(e) => setAnalysisName(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium">Primary objective</label>
              <select
                className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                value={objective}
                onChange={(e) => setObjective(e.target.value)}
              >
                {(objectives ?? [{ id: 'maximize_revenue', label: 'Maximize Revenue' }]).map(
                  (o) => (
                    <option key={o.id} value={o.id}>
                      {o.label}
                    </option>
                  ),
                )}
              </select>
            </div>
            <Button onClick={() => setStep(1)}>Continue</Button>
          </CardContent>
        </Card>
      )}

      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Select simulations</CardTitle>
            <CardDescription>
              Recommendations chain statistical → causal → simulation evidence
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {completedSims.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No completed simulations.{' '}
                <Link
                  to={`/app/datasets/${datasetId}/simulation?project_id=${projectId}`}
                  className="text-primary underline"
                >
                  Run simulation first
                </Link>
              </p>
            ) : (
              completedSims.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => toggleSim(s.id)}
                  className={cn(
                    'w-full rounded-lg border p-3 text-left text-sm',
                    selectedSims.includes(s.id) || selectedSims.length === 0
                      ? 'border-primary'
                      : 'opacity-60',
                  )}
                >
                  {s.name}
                </button>
              ))
            )}
            <Button className="mt-4" onClick={() => setStep(2)} disabled={completedSims.length === 0}>
              Continue
            </Button>
          </CardContent>
        </Card>
      )}

      {step === 2 && (
        <Card>
          <CardHeader>
            <CardTitle>Constraints & tolerance</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-3">
            <div>
              <label className="text-sm font-medium">Risk tolerance (0–1)</label>
              <Input value={riskTolerance} onChange={(e) => setRiskTolerance(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium">Min confidence (0–1)</label>
              <Input value={minConfidence} onChange={(e) => setMinConfidence(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium">Max budget</label>
              <Input value={maxBudget} onChange={(e) => setMaxBudget(e.target.value)} />
            </div>
            <Button
              className="sm:col-span-3"
              onClick={() => {
                void handleRun();
              }}
              disabled={runMutation.isPending}
            >
              {runMutation.isPending ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Play className="size-4" />
              )}
              Run decision engine
            </Button>
          </CardContent>
        </Card>
      )}

      {step === 3 && lastRun && <ResultsPanel run={lastRun} />}

      {history && history.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Decision history</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              {history.map((h) => (
                <li key={h.id} className="flex justify-between border-b py-2">
                  <span>{h.name}</span>
                  <span className="text-muted-foreground">{h.status}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
