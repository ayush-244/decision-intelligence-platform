import ReactECharts from 'echarts-for-react';
import { useMemo, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { Brain, Loader2, Play } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  useAnalyzeDatasetIntelligenceMutation,
  useDatasetIntelligenceQuery,
  type ColumnIntelligence,
  type IntelligenceReport,
} from '@/features/intelligence';
import { cn } from '@/lib/utils';

const TABS = [
  { id: 'summary', label: 'Summary' },
  { id: 'quality', label: 'Data Quality' },
  { id: 'columns', label: 'Column Explorer' },
  { id: 'correlations', label: 'Correlations' },
  { id: 'missing', label: 'Missing Data' },
  { id: 'outliers', label: 'Outliers' },
  { id: 'distributions', label: 'Distributions' },
] as const;

type TabId = (typeof TABS)[number]['id'];

function ScoreBadge({ label, score }: { label: string; score: number }) {
  const color = score >= 80 ? 'text-emerald-400' : score >= 60 ? 'text-amber-400' : 'text-red-400';
  return (
    <div className="bg-muted/50 rounded-lg p-4 text-center">
      <p className="text-muted-foreground text-xs tracking-wide uppercase">{label}</p>
      <p className={cn('text-3xl font-semibold tabular-nums', color)}>{score.toFixed(0)}</p>
    </div>
  );
}

function CorrelationHeatmap({ report }: { report: IntelligenceReport }) {
  const correlations = report.correlations as {
    heatmap?: { columns: string[]; values: (number | null)[][] };
  };
  const columns = useMemo(() => correlations.heatmap?.columns ?? [], [correlations]);
  const values = useMemo(() => correlations.heatmap?.values ?? [], [correlations]);

  const option = useMemo(
    () => ({
      tooltip: { position: 'top' },
      grid: { left: 80, right: 20, top: 20, bottom: 80 },
      xAxis: { type: 'category', data: columns, axisLabel: { rotate: 45, fontSize: 10 } },
      yAxis: { type: 'category', data: columns, axisLabel: { fontSize: 10 } },
      visualMap: {
        min: -1,
        max: 1,
        calculable: false,
        orient: 'horizontal',
        left: 'center',
        bottom: 0,
        // Diverging correlation scale: slate (−) → paper → vermilion (+).
        inRange: { color: ['#516b8f', '#f4f2ee', '#c2410c'] },
      },
      series: [
        {
          type: 'heatmap',
          data: values.flatMap((row, i) => row.map((val, j) => [j, i, val ?? 0])),
          label: { show: columns.length <= 8 },
        },
      ],
    }),
    [columns, values],
  );

  if (columns.length < 2) {
    return (
      <p className="text-muted-foreground text-sm">Not enough numeric columns for a heatmap.</p>
    );
  }

  return <ReactECharts option={option} theme="delphi" style={{ height: 360 }} />;
}

function displayText(value: unknown): string {
  if (value === null || value === undefined) return '';
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }
  return JSON.stringify(value);
}

function DistributionChart({ dist }: { dist: Record<string, unknown> }) {
  const histogram = dist.histogram as { bins: number[]; counts: number[] } | undefined;
  const column = displayText(dist.column);

  const option = useMemo(() => {
    if (!histogram?.bins?.length) return {};
    const labels = histogram.bins
      .slice(0, -1)
      .map((b, i) => `${b.toFixed(1)}–${histogram.bins[i + 1]?.toFixed(1)}`);
    return {
      title: { text: column, left: 'center', textStyle: { fontSize: 13 } },
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: labels, axisLabel: { rotate: 30, fontSize: 9 } },
      yAxis: { type: 'value' },
      series: [{ type: 'bar', data: histogram.counts }],
    };
  }, [column, histogram]);

  return <ReactECharts option={option} theme="delphi" style={{ height: 260 }} />;
}

function ColumnTable({ columns, filter }: { columns: ColumnIntelligence[]; filter: string }) {
  const q = filter.toLowerCase();
  const rows = columns.filter((c) => c.name.toLowerCase().includes(q));

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left">
            <th className="px-2 py-2">Column</th>
            <th className="px-2 py-2">Type</th>
            <th className="px-2 py-2">Role</th>
            <th className="px-2 py-2">Null %</th>
            <th className="px-2 py-2">Distinct</th>
            <th className="px-2 py-2">Usability</th>
            <th className="px-2 py-2">Issues</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((col) => (
            <tr key={col.name} className="hover:bg-muted/30 border-b">
              <td className="px-2 py-2 font-medium">{col.name}</td>
              <td className="px-2 py-2">{col.semantic_type}</td>
              <td className="px-2 py-2">{col.suggested_role}</td>
              <td className="px-2 py-2 tabular-nums">{col.null_percentage}%</td>
              <td className="px-2 py-2 tabular-nums">{col.distinct_count}</td>
              <td className="px-2 py-2 tabular-nums">{col.usability_score}</td>
              <td className="text-muted-foreground px-2 py-2 text-xs">
                {col.potential_issues.join('; ') || '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function DatasetIntelligencePage() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const [searchParams] = useSearchParams();
  const projectId = searchParams.get('project_id') ?? '';
  const versionId = searchParams.get('version_id') ?? undefined;
  const [tab, setTab] = useState<TabId>('summary');
  const [columnFilter, setColumnFilter] = useState('');

  const report = useDatasetIntelligenceQuery(datasetId, versionId);
  const analyze = useAnalyzeDatasetIntelligenceMutation();

  const needsAnalysis = report.isError || (report.isSuccess && !report.data?.overview);

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Brain className="size-5" />
            <h1 className="text-display text-2xl sm:text-[1.75rem]">Data Intelligence</h1>
          </div>
          <p className="text-muted-foreground mt-1 text-sm">
            Automated data understanding — quality, structure, relationships, and analytical
            readiness.
          </p>
        </div>
        <div className="flex gap-2">
          <Button asChild variant="outline" size="sm">
            <Link to={`/app/datasets/${datasetId}?project_id=${projectId}`}>Back to dataset</Link>
          </Button>
          <Button
            size="sm"
            disabled={!datasetId || analyze.isPending}
            onClick={() => {
              if (!datasetId) return;
              void analyze.mutateAsync({ datasetId, ...(versionId ? { versionId } : {}) });
            }}
          >
            {analyze.isPending ? (
              <Loader2 className="mr-2 size-4 animate-spin" />
            ) : (
              <Play className="mr-2 size-4" />
            )}
            Run analysis
          </Button>
        </div>
      </div>

      {report.isLoading ? (
        <Card>
          <CardContent className="text-muted-foreground flex items-center gap-2 py-12">
            <Loader2 className="size-4 animate-spin" /> Loading intelligence report…
          </CardContent>
        </Card>
      ) : null}

      {needsAnalysis && !report.isLoading ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">No intelligence report yet</CardTitle>
            <CardDescription>
              Run analysis to generate quality scores, column intelligence, correlations, and
              readiness assessment for this dataset version.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : null}

      {report.data ? (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            <ScoreBadge label="Quality Score" score={report.data.data_quality.overall_score} />
            <ScoreBadge
              label="Health Score"
              score={report.data.data_health.overall_score ?? report.data.health_score ?? 0}
            />
            <div className="bg-muted/50 rounded-lg p-4 text-center">
              <p className="text-muted-foreground text-xs tracking-wide uppercase">Rows sampled</p>
              <p className="text-3xl font-semibold tabular-nums">
                {report.data.rows_sampled.toLocaleString()}
                <span className="text-muted-foreground text-base font-normal">
                  {' '}
                  / {report.data.total_rows.toLocaleString()}
                </span>
              </p>
            </div>
          </div>

          <div className="flex flex-wrap gap-2 border-b pb-2">
            {TABS.map((item) => (
              <button
                key={item.id}
                type="button"
                className={cn(
                  'rounded-md px-3 py-1.5 text-sm transition-colors',
                  tab === item.id
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-muted',
                )}
                onClick={() => setTab(item.id)}
              >
                {item.label}
              </button>
            ))}
          </div>

          {tab === 'summary' ? (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Overview</CardTitle>
                <CardDescription>
                  Trust level:{' '}
                  <span className="capitalize">{report.data.overview.trust_level}</span>
                  {' · '}v{report.data.overview.version_number} ·{' '}
                  {report.data.overview.row_count.toLocaleString()} rows
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <ul className="list-disc space-y-1 pl-5 text-sm">
                  {report.data.overview.headline_findings.map((f: string) => (
                    <li key={f}>{f}</li>
                  ))}
                </ul>
                {report.data.recommendations.length > 0 ? (
                  <div>
                    <h3 className="mb-2 text-sm font-medium">Recommendations</h3>
                    <ul className="text-muted-foreground list-disc space-y-1 pl-5 text-sm">
                      {report.data.recommendations.map((r: string) => (
                        <li key={r}>{r}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </CardContent>
            </Card>
          ) : null}

          {tab === 'quality' ? (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Data Quality</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2 text-sm">
                  <p>Completeness: {report.data.data_quality.completeness}%</p>
                  <p>Uniqueness: {report.data.data_quality.uniqueness}%</p>
                  <p>Consistency: {report.data.data_quality.consistency}%</p>
                  <p>Duplicates: {report.data.data_quality.duplicate_percentage}%</p>
                </div>
                <div>
                  <h3 className="mb-2 text-sm font-medium">Issues</h3>
                  <ul className="text-muted-foreground list-disc space-y-1 pl-5 text-sm">
                    {report.data.data_quality.issues.map((issue: string) => (
                      <li key={issue}>{issue}</li>
                    ))}
                  </ul>
                </div>
              </CardContent>
            </Card>
          ) : null}

          {tab === 'columns' ? (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Column Explorer</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Input
                  placeholder="Search columns…"
                  value={columnFilter}
                  onChange={(e) => setColumnFilter(e.target.value)}
                  className="max-w-xs"
                />
                <ColumnTable columns={report.data.columns} filter={columnFilter} />
              </CardContent>
            </Card>
          ) : null}

          {tab === 'correlations' ? (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Correlation Explorer</CardTitle>
              </CardHeader>
              <CardContent>
                <CorrelationHeatmap report={report.data} />
              </CardContent>
            </Card>
          ) : null}

          {tab === 'missing' ? (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Missing Data</CardTitle>
                <CardDescription>
                  Overall missing:{' '}
                  {String(
                    (report.data.missing_data as { overall_missing_percentage?: number })
                      .overall_missing_percentage ?? 0,
                  )}
                  %
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="text-muted-foreground list-disc space-y-1 pl-5 text-sm">
                  {(
                    (report.data.missing_data as { imputation_hints?: string[] })
                      .imputation_hints ?? []
                  ).map((hint) => (
                    <li key={hint}>{hint}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ) : null}

          {tab === 'outliers' ? (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Outlier Explorer</CardTitle>
                <CardDescription>
                  {String((report.data.outliers as { summary?: string }).summary ?? '')}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left">
                        <th className="px-2 py-2">Column</th>
                        <th className="px-2 py-2">Outliers</th>
                        <th className="px-2 py-2">%</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(
                        (
                          report.data.outliers as {
                            columns?: {
                              column: string;
                              outlier_count: number;
                              outlier_percentage: number;
                            }[];
                          }
                        ).columns ?? []
                      ).map((row) => (
                        <tr key={row.column} className="border-b">
                          <td className="px-2 py-2">{row.column}</td>
                          <td className="px-2 py-2">{row.outlier_count}</td>
                          <td className="px-2 py-2">{row.outlier_percentage}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          ) : null}

          {tab === 'distributions' ? (
            <div className="grid gap-4 md:grid-cols-2">
              {(report.data.distributions ?? []).map((dist: Record<string, unknown>) => (
                <Card key={displayText(dist.column)}>
                  <CardContent className="pt-4">
                    <DistributionChart dist={dist} />
                    <p className="text-muted-foreground mt-2 text-xs">
                      {displayText(dist.interpretation)}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
