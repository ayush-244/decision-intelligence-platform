import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  addEdge,
  useEdgesState,
  useNodesState,
  type Connection,
  type Edge,
  type Node,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import ReactECharts from 'echarts-for-react';
import { useCallback, useMemo, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { Loader2, Network, Play } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  useCreateDAGMutation,
  useCausalHistoryQuery,
  useRunCausalAnalysisMutation,
  type CausalAnalysisRun,
  type DAGNode,
} from '@/features/causal';
import { cn } from '@/lib/utils';

const STEPS = ['Question', 'Variables', 'DAG', 'Results'] as const;

/** Variable roles use the Delphi visualization palette (see lib/chart-theme). */
const ROLE_COLORS: Record<string, string> = {
  treatment: '#c2410c', // vermilion — the intervention is the signal
  outcome: '#4d7c5f', // moss
  confounder: '#b45309', // ochre
  mediator: '#86589b', // plum
  unknown: '#64748b', // slate
};

function nodeStyle(role?: string) {
  const color = ROLE_COLORS[role ?? 'unknown'] ?? ROLE_COLORS.unknown;
  return {
    border: `2px solid ${color}`,
    borderRadius: 8,
    padding: 8,
    background: `${color}22`,
    fontSize: 12,
  };
}

function TreatmentEffectChart({ run }: { run: CausalAnalysisRun }) {
  const te = run.result.treatment_effect;
  const option = useMemo(
    () => ({
      tooltip: {},
      xAxis: { type: 'category', data: ['ATE', 'ATT', 'ATC'] },
      yAxis: { type: 'value', name: 'Effect' },
      series: [
        {
          type: 'bar',
          data: [te.ate, te.att, te.atc].map((v) => (v != null ? v : 0)),
        },
      ],
    }),
    [te],
  );
  return <ReactECharts option={option} theme="delphi" style={{ height: 220 }} />;
}

function ResultPanel({ run }: { run: CausalAnalysisRun }) {
  const interp = run.result.interpretation;
  const id = run.result.identification;
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Treatment effect</CardTitle>
          <CardDescription>
            Estimator: {run.result.treatment_effect.estimator.replace(/_/g, ' ')}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <TreatmentEffectChart run={run} />
          <p className="text-sm">
            ATE: {run.result.treatment_effect.ate?.toFixed(4) ?? '—'}
            {run.result.treatment_effect.ci_lower != null && (
              <> · CI [{run.result.treatment_effect.ci_lower.toFixed(4)}, {run.result.treatment_effect.ci_upper?.toFixed(4)}]</>
            )}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Identification</CardTitle>
          <CardDescription>{id.strategy.replace(/_/g, ' ')}</CardDescription>
        </CardHeader>
        <CardContent className="text-muted-foreground space-y-2 text-sm">
          <p>{id.reasoning}</p>
          {id.adjustment_set.length > 0 && (
            <p>Adjustment set: {id.adjustment_set.join(', ')}</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Business interpretation</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p>{interp.business_interpretation}</p>
          <p className={cn('font-medium', interp.causal_claim_valid ? 'text-emerald-400' : 'text-amber-400')}>
            Causal claim valid: {interp.causal_claim_valid ? 'Yes (under stated assumptions)' : 'No — review assumptions'}
          </p>
          <div>
            <p className="mb-1 font-medium">Limitations</p>
            <ul className="text-muted-foreground list-inside list-disc">
              {interp.limitations.map((l) => (
                <li key={l}>{l}</li>
              ))}
            </ul>
          </div>
        </CardContent>
      </Card>

      {run.result.refutation_results.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Refutation</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {run.result.refutation_results.map((r) => (
              <div
                key={r.method}
                className={cn(
                  'rounded-md border px-3 py-2 text-sm',
                  r.passed ? 'border-emerald-500/30' : 'border-amber-500/30',
                )}
              >
                <p className="font-medium">{r.method.replace(/_/g, ' ')}</p>
                <p className="text-muted-foreground">{r.explanation}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export function DatasetCausalPage() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const [searchParams] = useSearchParams();
  const projectId = searchParams.get('project_id') ?? '';

  const [step, setStep] = useState(0);
  const [question, setQuestion] = useState('');
  const [treatment, setTreatment] = useState('treatment');
  const [outcome, setOutcome] = useState('outcome');
  const [columnInput, setColumnInput] = useState('confounder,treatment,outcome');
  const [completedRun, setCompletedRun] = useState<CausalAnalysisRun | null>(null);
  const [savedDagId, setSavedDagId] = useState<string | null>(null);

  const historyQuery = useCausalHistoryQuery(datasetId);
  const runMutation = useRunCausalAnalysisMutation();
  const createDagMutation = useCreateDAGMutation();

  const initialNodes: Node[] = useMemo(
    () => [
      { id: 'confounder', position: { x: 80, y: 40 }, data: { label: 'confounder' }, style: nodeStyle('confounder') },
      { id: 'treatment', position: { x: 40, y: 160 }, data: { label: 'treatment' }, style: nodeStyle('treatment') },
      { id: 'outcome', position: { x: 220, y: 160 }, data: { label: 'outcome' }, style: nodeStyle('outcome') },
    ],
    [],
  );
  const initialEdges: Edge[] = useMemo(
    () => [
      { id: 'c-t', source: 'confounder', target: 'treatment' },
      { id: 'c-y', source: 'confounder', target: 'outcome' },
      { id: 't-y', source: 'treatment', target: 'outcome' },
    ],
    [],
  );

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (connection: Connection) => setEdges((eds) => addEdge(connection, eds)),
    [setEdges],
  );

  const buildDagPayload = () => {
    const dagNodes: DAGNode[] = nodes.map((n) => ({
      id: n.id,
      label: typeof n.data.label === 'string' ? n.data.label : n.id,
      role: n.id === treatment ? 'treatment' : n.id === outcome ? 'outcome' : 'confounder',
      position: n.position,
    }));
    const dagEdges = edges.map((e) => ({ source: e.source, target: e.target }));
    const roles = Object.fromEntries(
      dagNodes.map((n) => [n.id, n.role ?? 'unknown']),
    );
    return { nodes: dagNodes, edges: dagEdges, variable_roles: roles };
  };

  const handleSaveDag = async () => {
    if (!datasetId) return;
    const payload = buildDagPayload();
    const dag = await createDagMutation.mutateAsync({
      dataset_id: datasetId,
      name: `DAG — ${treatment} → ${outcome}`,
      ...payload,
    });
    setSavedDagId(dag.id);
    toast.success('DAG saved');
    setStep(3);
  };

  const handleRun = async () => {
    if (!datasetId) return;
    let dagId = savedDagId;
    if (!dagId) {
      const payload = buildDagPayload();
      const dag = await createDagMutation.mutateAsync({
        dataset_id: datasetId,
        name: `DAG — ${treatment} → ${outcome}`,
        ...payload,
      });
      dagId = dag.id;
      setSavedDagId(dagId);
    }
    const run = await runMutation.mutateAsync({
      dataset_id: datasetId,
      dag_id: dagId,
      treatment,
      outcome,
      business_question: question || `Effect of ${treatment} on ${outcome}`,
      run_refutation: true,
      run_sensitivity: true,
    });
    setCompletedRun(run);
    setStep(3);
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-display flex items-center gap-2 text-2xl sm:text-[1.75rem]">
            <Network className="h-6 w-6" />
            Causal Inference
          </h1>
          <p className="text-muted-foreground mt-1 text-sm">
            Model assumptions explicitly. Never confuse correlation with causation.
          </p>
        </div>
        <Link to={`/app/datasets/${datasetId}?project_id=${projectId}`}>
          <Button variant="outline" size="sm">Back to dataset</Button>
        </Link>
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
            <CardTitle>Business question</CardTitle>
            <CardDescription>What causal effect do you want to estimate?</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. Does increasing marketing spend cause higher revenue?"
            />
            <Button onClick={() => setStep(1)}>Continue</Button>
          </CardContent>
        </Card>
      )}

      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Treatment & outcome</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium">Treatment column</label>
              <Input value={treatment} onChange={(e) => setTreatment(e.target.value)} />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">Outcome column</label>
              <Input value={outcome} onChange={(e) => setOutcome(e.target.value)} />
            </div>
            <div className="sm:col-span-2">
              <label className="mb-1 block text-sm font-medium">All columns (comma-separated)</label>
              <Input value={columnInput} onChange={(e) => setColumnInput(e.target.value)} />
            </div>
            <div className="flex gap-2 sm:col-span-2">
              <Button variant="outline" onClick={() => setStep(0)}>Back</Button>
              <Button onClick={() => setStep(2)}>Build DAG</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {step === 2 && (
        <Card>
          <CardHeader>
            <CardTitle>DAG builder</CardTitle>
            <CardDescription>
              Drag nodes, connect edges. Arrows indicate assumed causal direction.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="h-[400px] rounded-lg border">
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                fitView
              >
                <Background />
                <Controls />
                <MiniMap />
              </ReactFlow>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setStep(1)}>Back</Button>
              <Button
                onClick={() => {
                  void handleSaveDag();
                }}
                disabled={createDagMutation.isPending}
              >
                Save DAG
              </Button>
              <Button
                onClick={() => {
                  void handleRun();
                }}
                disabled={runMutation.isPending}
              >
                {runMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
                Run analysis
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {step === 3 && completedRun && <ResultPanel run={completedRun} />}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Analysis history</CardTitle>
        </CardHeader>
        <CardContent>
          {historyQuery.data?.length ? (
            <ul className="space-y-2 text-sm">
              {historyQuery.data.map((item) => (
                <li key={item.id} className="flex justify-between rounded-md border px-3 py-2">
                  <span>{item.treatment} → {item.outcome}</span>
                  <span className="text-muted-foreground">{item.status}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-muted-foreground text-sm">No analyses yet.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
