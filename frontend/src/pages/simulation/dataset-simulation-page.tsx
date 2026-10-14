import ReactECharts from 'echarts-for-react';
import { useMemo, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { FlaskConical, Loader2, Play } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  useCausalModelsQuery,
  useRunSimulationMutation,
  useSimulationHistoryQuery,
  type SimulationRun,
} from '@/features/simulation';
import { cn } from '@/lib/utils';

const STEPS = ['Causal Model', 'Scenario', 'Assumptions', 'Results'] as const;

function MonteCarloChart({ run }: { run: SimulationRun }) {
  const mc = run.result.monte_carlo;
  const option = useMemo(
    () => ({
      tooltip: {},
      xAxis: { type: 'category', name: 'Percentile', data: ['P5', 'P25', 'Median', 'P75', 'P95'] },
      yAxis: { type: 'value', name: 'Outcome' },
      series: [
        {
          type: 'line',
          smooth: true,
          data: [mc.p05, mc.p25, mc.median, mc.p75, mc.p95],
          areaStyle: { opacity: 0.12 },
        },
      ],
    }),
    [mc],
  );
  return <ReactECharts option={option} theme="delphi" style={{ height: 240 }} />;
}

function ResultPanel({ run }: { run: SimulationRun }) {
  const r = run.result;
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Counterfactual outcome</CardTitle>
          <CardDescription>Not a forecast — grounded in causal treatment effects</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Metric label="Baseline" value={r.counterfactual.baseline_outcome.toFixed(2)} />
          <Metric label="Expected" value={r.counterfactual.expected_outcome.toFixed(2)} />
          <Metric
            label="CI"
            value={`${r.counterfactual.ci_lower.toFixed(2)} – ${r.counterfactual.ci_upper.toFixed(2)}`}
          />
          <Metric
            label="P(improve)"
            value={`${(r.counterfactual.probability_improvement * 100).toFixed(0)}%`}
          />
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Monte Carlo distribution</CardTitle>
            <CardDescription>{r.monte_carlo.methodology}</CardDescription>
          </CardHeader>
          <CardContent>
            <MonteCarloChart run={run} />
            <p className="mt-2 text-sm text-muted-foreground">
              Tail risk (worse than baseline): {(r.monte_carlo.tail_risk * 100).toFixed(1)}%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Risk & ROI</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <p>
              <span className="font-medium">Risk score:</span>{' '}
              {(r.risk.overall_score * 100).toFixed(0)}% — {r.risk.summary}
            </p>
            <p>
              <span className="font-medium">Expected ROI:</span>{' '}
              {(r.roi.expected_roi * 100).toFixed(1)}%
            </p>
            <p>
              <span className="font-medium">Cost / benefit:</span> {r.roi.expected_cost.toFixed(0)}{' '}
              cost → {r.roi.expected_revenue.toFixed(0)} revenue
            </p>
            {r.constraint_evaluations.map((c, i) => (
              <p key={i} className={cn(!c.satisfied && 'text-amber-600')}>
                {c.message}
              </p>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Business interpretation</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p>{r.interpretation.business_interpretation}</p>
          <div>
            <p className="font-medium">Limitations</p>
            <ul className="list-disc pl-5 text-muted-foreground">
              {r.interpretation.limitations.map((l, i) => (
                <li key={i}>{l}</li>
              ))}
            </ul>
          </div>
          <div>
            <p className="font-medium">Recommended actions</p>
            <ul className="list-disc pl-5">
              {r.interpretation.recommended_actions.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-lg font-semibold">{value}</p>
    </div>
  );
}

export function DatasetSimulationPage() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const [searchParams] = useSearchParams();
  const projectId = searchParams.get('project_id') ?? '';

  const [step, setStep] = useState(0);
  const [causalAnalysisId, setCausalAnalysisId] = useState('');
  const [scenarioName, setScenarioName] = useState('Intervention scenario');
  const [objective, setObjective] = useState('What happens if we change the treatment?');
  const [interventionPct, setInterventionPct] = useState('0.2');
  const [treatmentVar, setTreatmentVar] = useState('treatment');
  const [revenuePerUnit, setRevenuePerUnit] = useState('100');
  const [interventionCost, setInterventionCost] = useState('500');
  const [lastRun, setLastRun] = useState<SimulationRun | null>(null);

  const { data: causalModels, isLoading: loadingModels } = useCausalModelsQuery(datasetId);
  const { data: history } = useSimulationHistoryQuery(datasetId);
  const runMutation = useRunSimulationMutation(datasetId);

  const completedModels = (causalModels ?? []).filter((m) => m.status === 'completed');

  const handleRun = async () => {
    if (!datasetId || !causalAnalysisId) {
      toast.error('Select a completed causal model');
      return;
    }
    const run = await runMutation.mutateAsync({
      dataset_id: datasetId,
      causal_analysis_id: causalAnalysisId,
      name: scenarioName,
      objective,
      interventions: [
        {
          variable: treatmentVar,
          mode: 'relative',
          value: parseFloat(interventionPct) || 0,
          reason: 'User-defined intervention',
        },
      ],
      monte_carlo_iterations: 500,
      roi_assumptions: {
        revenue_per_outcome_unit: parseFloat(revenuePerUnit) || 1,
        intervention_cost: parseFloat(interventionCost) || 0,
      },
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
            <FlaskConical className="size-6" />
            Decision Simulation
          </h1>
          <p className="text-sm text-muted-foreground">
            Evaluate interventions using causal models — not predictive forecasting
          </p>
        </div>
        <Button asChild variant="outline" size="sm">
          <Link to={`/app/datasets/${datasetId}?project_id=${projectId}`}>Back to dataset</Link>
        </Button>
      </div>

      <div className="flex gap-2">
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
            <CardTitle>Choose causal model</CardTitle>
            <CardDescription>
              Simulations build on Phase 6 causal estimates. Run causal analysis first if none exist.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {loadingModels ? (
              <Loader2 className="size-6 animate-spin" />
            ) : completedModels.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No completed causal models.{' '}
                <Link
                  to={`/app/datasets/${datasetId}/causal?project_id=${projectId}`}
                  className="text-primary underline"
                >
                  Run causal analysis
                </Link>
              </p>
            ) : (
              <div className="space-y-2">
                {completedModels.map((m) => (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => {
                      setCausalAnalysisId(m.id);
                      setTreatmentVar(m.treatment);
                      setStep(1);
                    }}
                    className={cn(
                      'w-full rounded-lg border p-3 text-left text-sm hover:bg-muted/50',
                      causalAnalysisId === m.id && 'border-primary',
                    )}
                  >
                    <span className="font-medium">
                      {m.treatment} → {m.outcome}
                    </span>
                    <span className="ml-2 text-muted-foreground">({m.id.slice(0, 8)}…)</span>
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Define scenario</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="text-sm font-medium">Scenario name</label>
              <Input value={scenarioName} onChange={(e) => setScenarioName(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium">Objective</label>
              <Input value={objective} onChange={(e) => setObjective(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium">Treatment variable</label>
              <Input value={treatmentVar} onChange={(e) => setTreatmentVar(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium">Relative change (e.g. 0.2 = +20%)</label>
              <Input value={interventionPct} onChange={(e) => setInterventionPct(e.target.value)} />
            </div>
            <Button className="sm:col-span-2" onClick={() => setStep(2)}>
              Continue
            </Button>
          </CardContent>
        </Card>
      )}

      {step === 2 && (
        <Card>
          <CardHeader>
            <CardTitle>Business assumptions</CardTitle>
            <CardDescription>ROI inputs are configurable and shown in the report</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="text-sm font-medium">Revenue per outcome unit</label>
              <Input value={revenuePerUnit} onChange={(e) => setRevenuePerUnit(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium">Intervention cost</label>
              <Input value={interventionCost} onChange={(e) => setInterventionCost(e.target.value)} />
            </div>
            <Button
              className="sm:col-span-2"
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
              Run simulation
            </Button>
          </CardContent>
        </Card>
      )}

      {step === 3 && lastRun && <ResultPanel run={lastRun} />}

      {history && history.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Simulation history</CardTitle>
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
