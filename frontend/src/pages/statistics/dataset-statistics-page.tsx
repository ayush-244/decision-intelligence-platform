import ReactECharts from 'echarts-for-react';
import { useMemo, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { BarChart3, ChevronRight, History, Loader2, Sparkles } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  ANALYSIS_GOALS,
  VARIABLE_ROLES,
  useAnalysisHistoryQuery,
  useRecommendationsMutation,
  useRunAnalysisMutation,
  type AnalysisRun,
  type VariableSpec,
} from '@/features/statistics';
import { cn } from '@/lib/utils';

const WIZARD_STEPS = ['Goal', 'Variables', 'Recommendation', 'Results'] as const;

function AssumptionPanel({ run }: { run: AnalysisRun }) {
  const checks = run.result?.assumption_report?.checks ?? [];
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Assumption validation</CardTitle>
        <CardDescription>
          {run.result.assumption_report.all_passed
            ? 'All checked assumptions passed.'
            : 'Some assumptions were violated — review alternatives.'}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {checks.map((c) => (
          <div
            key={c.name}
            className={cn(
              'rounded-md border px-3 py-2 text-sm',
              c.status === 'passed' && 'border-emerald-500/30 bg-emerald-500/5',
              c.status === 'failed' && 'border-red-500/30 bg-red-500/5',
              c.status === 'warning' && 'border-amber-500/30 bg-amber-500/5',
            )}
          >
            <p className="font-medium">{c.name}</p>
            <p className="text-muted-foreground">{c.explanation}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function EffectSizeViewer({ run }: { run: AnalysisRun }) {
  const sizes = useMemo(() => run.result?.effect_sizes ?? [], [run]);
  const option = useMemo(
    () => ({
      tooltip: {},
      xAxis: { type: 'category', data: sizes.map((e) => e.name) },
      yAxis: { type: 'value', name: 'Effect size' },
      series: [
        {
          type: 'bar',
          data: sizes.map((e) => ({
            value: e.value,
            itemStyle: {
              // Delphi palette: large effects carry the signal color.
              color:
                e.magnitude === 'large'
                  ? '#c2410c'
                  : e.magnitude === 'medium'
                    ? '#b45309'
                    : '#64748b',
            },
          })),
        },
      ],
    }),
    [sizes],
  );
  if (!sizes.length) {
    return (
      <p className="text-muted-foreground text-sm">
        Effect size not available for this analysis type.
      </p>
    );
  }
  return (
    <div className="space-y-3">
      <ReactECharts option={option} theme="delphi" style={{ height: 220 }} />
      {sizes.map((e) => (
        <p key={e.name} className="text-sm">
          <span className="font-medium">{e.name}</span> ({e.magnitude}): {e.interpretation}
        </p>
      ))}
    </div>
  );
}

function ConfidenceIntervalViewer({ run }: { run: AnalysisRun }) {
  const intervals = run.result?.confidence_intervals ?? [];
  if (!intervals.length) {
    return <p className="text-muted-foreground text-sm">No confidence intervals for this test.</p>;
  }
  return (
    <div className="space-y-3">
      {intervals.map((ci) => (
        <div key={ci.parameter} className="rounded-md border p-3 text-sm">
          <p className="font-medium">{ci.parameter}</p>
          <p className="tabular-nums">
            [{ci.lower.toFixed(4)}, {ci.upper.toFixed(4)}] at {(ci.level * 100).toFixed(0)}%
          </p>
          <p className="text-muted-foreground mt-1">{ci.interpretation}</p>
        </div>
      ))}
    </div>
  );
}

function ResultExplorer({ run }: { run: AnalysisRun }) {
  const interp = run.result?.interpretation;
  const test = run.result?.test_result;
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{interp?.test_performed ?? run.test_type}</CardTitle>
          <CardDescription>{interp?.selection_reason}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {test && (
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="bg-muted/50 rounded-lg p-3 text-center">
                <p className="text-muted-foreground text-xs">p-value</p>
                <p className="text-2xl font-semibold tabular-nums">
                  {test.p_value != null ? test.p_value.toFixed(4) : '—'}
                </p>
              </div>
              <div className="bg-muted/50 rounded-lg p-3 text-center">
                <p className="text-muted-foreground text-xs">Statistic</p>
                <p className="text-2xl font-semibold tabular-nums">
                  {test.statistic != null ? test.statistic.toFixed(4) : '—'}
                </p>
              </div>
              <div className="bg-muted/50 rounded-lg p-3 text-center">
                <p className="text-muted-foreground text-xs">Significant</p>
                <p
                  className={cn(
                    'text-2xl font-semibold',
                    test.is_significant ? 'text-emerald-400' : 'text-muted-foreground',
                  )}
                >
                  {test.is_significant ? 'Yes' : 'No'}
                </p>
              </div>
            </div>
          )}
          <div>
            <p className="mb-1 text-sm font-medium">Business interpretation</p>
            <p className="text-muted-foreground text-sm">{interp?.business_interpretation}</p>
          </div>
          <div>
            <p className="mb-1 text-sm font-medium">Practical significance</p>
            <p className="text-muted-foreground text-sm">{interp?.practical_significance}</p>
          </div>
          {interp?.limitations?.length ? (
            <div>
              <p className="mb-1 text-sm font-medium">Limitations</p>
              <ul className="text-muted-foreground list-inside list-disc text-sm">
                {interp.limitations.map((l) => (
                  <li key={l}>{l}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {interp?.recommended_next_steps?.length ? (
            <div>
              <p className="mb-1 text-sm font-medium">Recommended next steps</p>
              <ul className="list-inside list-disc text-sm">
                {interp.recommended_next_steps.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Effect sizes</CardTitle>
          </CardHeader>
          <CardContent>
            <EffectSizeViewer run={run} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Confidence intervals</CardTitle>
          </CardHeader>
          <CardContent>
            <ConfidenceIntervalViewer run={run} />
          </CardContent>
        </Card>
      </div>

      <AssumptionPanel run={run} />
    </div>
  );
}

export function DatasetStatisticsPage() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const [searchParams] = useSearchParams();
  const projectId = searchParams.get('project_id') ?? undefined;

  const [step, setStep] = useState(0);
  const [goal, setGoal] = useState(ANALYSIS_GOALS[1]!.value);
  const [researchQuestion, setResearchQuestion] = useState('');
  const [columnInput, setColumnInput] = useState('value,group');
  const [variables, setVariables] = useState<VariableSpec[]>([
    { name: 'value', role: 'outcome' },
    { name: 'group', role: 'grouping' },
  ]);
  const [completedRun, setCompletedRun] = useState<AnalysisRun | null>(null);

  const historyQuery = useAnalysisHistoryQuery(datasetId);
  const recommendMutation = useRecommendationsMutation();
  const runMutation = useRunAnalysisMutation();

  const parseColumns = () => {
    const names = columnInput
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);
    if (!names.length) return;
    setVariables(
      names.map((name, i) => ({
        name,
        role: i === 0 ? 'outcome' : i === 1 ? 'grouping' : 'covariate',
      })),
    );
  };

  const handleRecommend = async () => {
    if (!datasetId) return;
    parseColumns();
    await recommendMutation.mutateAsync({
      datasetId,
      goal,
      variables,
    });
    setStep(2);
  };

  const handleRun = async () => {
    if (!datasetId) return;
    const run = await runMutation.mutateAsync({
      dataset_id: datasetId,
      goal,
      research_question: researchQuestion || `Analysis: ${goal}`,
      variables,
    });
    setCompletedRun(run);
    setStep(3);
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="text-muted-foreground mb-1 flex items-center gap-2 text-sm">
            <Link to={projectId ? `/app/datasets?project_id=${projectId}` : '/app/datasets'}>
              Datasets
            </Link>
            <ChevronRight className="h-3 w-3" />
            <span>Statistical Analysis</span>
          </div>
          <h1 className="text-display flex items-center gap-2 text-2xl sm:text-[1.75rem]">
            <BarChart3 className="h-6 w-6" />
            Statistical Analysis
          </h1>
          <p className="text-muted-foreground mt-1 text-sm">
            Describe your research question — Delphi recommends and runs the appropriate test.
          </p>
        </div>
        <Link to={`/app/datasets/${datasetId}/intelligence?project_id=${projectId ?? ''}`}>
          <Button variant="outline" size="sm">
            Data Intelligence
          </Button>
        </Link>
      </div>

      <div className="flex gap-2">
        {WIZARD_STEPS.map((label, i) => (
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
            <CardTitle>What do you want to learn?</CardTitle>
            <CardDescription>Select a research goal and describe your question.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-2 sm:grid-cols-2">
              {ANALYSIS_GOALS.map((g) => (
                <button
                  key={g.value}
                  type="button"
                  onClick={() => setGoal(g.value)}
                  className={cn(
                    'rounded-lg border p-3 text-left text-sm transition',
                    goal === g.value ? 'border-primary bg-primary/5' : 'hover:bg-muted/50',
                  )}
                >
                  <p className="font-medium">{g.label}</p>
                  <p className="text-muted-foreground">{g.description}</p>
                </button>
              ))}
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">Research question</label>
              <Input
                value={researchQuestion}
                onChange={(e) => setResearchQuestion(e.target.value)}
                placeholder="e.g. Do treatment and control groups differ in revenue?"
              />
            </div>
            <Button onClick={() => setStep(1)}>Continue</Button>
          </CardContent>
        </Card>
      )}

      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Assign variables</CardTitle>
            <CardDescription>
              Enter column names (comma-separated) and assign roles.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              value={columnInput}
              onChange={(e) => setColumnInput(e.target.value)}
              onBlur={parseColumns}
              placeholder="outcome_col, grouping_col"
            />
            <div className="space-y-2">
              {variables.map((v, i) => (
                <div key={v.name} className="flex items-center gap-2">
                  <span className="w-32 truncate text-sm font-medium">{v.name}</span>
                  <select
                    className="bg-background border-input rounded-md border px-2 py-1 text-sm"
                    value={v.role}
                    onChange={(e) => {
                      const next = [...variables];
                      next[i] = { ...v, role: e.target.value as VariableSpec['role'] };
                      setVariables(next);
                    }}
                  >
                    {VARIABLE_ROLES.map((r) => (
                      <option key={r.value} value={r.value}>
                        {r.label}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setStep(0)}>
                Back
              </Button>
              <Button
                onClick={() => {
                  void handleRecommend();
                }}
                disabled={recommendMutation.isPending}
              >
                {recommendMutation.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="mr-2 h-4 w-4" />
                )}
                Get recommendation
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {step === 2 && recommendMutation.data && (
        <Card>
          <CardHeader>
            <CardTitle>Recommended analysis</CardTitle>
            <CardDescription>
              {recommendMutation.data.recommended_test.replace(/_/g, ' ')}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm">{recommendMutation.data.reasoning}</p>
            <div>
              <p className="mb-1 text-sm font-medium">Expected assumptions</p>
              <ul className="text-muted-foreground list-inside list-disc text-sm">
                {recommendMutation.data.expected_assumptions.map((a) => (
                  <li key={a}>{a}</li>
                ))}
              </ul>
            </div>
            {recommendMutation.data.alternatives.length > 0 && (
              <div>
                <p className="mb-1 text-sm font-medium">Alternatives if assumptions fail</p>
                <p className="text-muted-foreground text-sm">
                  {recommendMutation.data.alternatives.join(', ')}
                </p>
              </div>
            )}
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setStep(1)}>
                Back
              </Button>
              <Button
                onClick={() => {
                  void handleRun();
                }}
                disabled={runMutation.isPending}
              >
                {runMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Run analysis
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {step === 3 && completedRun && <ResultExplorer run={completedRun} />}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <History className="h-4 w-4" />
            Analysis history
          </CardTitle>
        </CardHeader>
        <CardContent>
          {historyQuery.isLoading ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : !historyQuery.data?.length ? (
            <p className="text-muted-foreground text-sm">No analyses yet.</p>
          ) : (
            <ul className="space-y-2">
              {historyQuery.data.map((item) => (
                <li
                  key={item.id}
                  className="hover:bg-muted/50 flex items-center justify-between rounded-md border px-3 py-2 text-sm"
                >
                  <span>
                    {item.goal} · {item.test_type ?? 'pending'}
                  </span>
                  <span className="text-muted-foreground text-xs">
                    {new Date(item.created_at).toLocaleString()}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
