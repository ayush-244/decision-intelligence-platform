import { Activity, Database, Gauge, Layers, Server } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  useCacheStatsQuery,
  useCancelJobMutation,
  useInfrastructureMetricsQuery,
  useJobsQuery,
  useQueueStatusQuery,
  useRetryJobMutation,
  useSubmitJobMutation,
} from '@/features/infrastructure';
import { cn } from '@/lib/utils';

/** Safe display of loosely-typed metric values from the API. */
function asMetric(value: unknown): string {
  if (typeof value === 'string' && value.length > 0) return value;
  if (typeof value === 'number') return String(value);
  return '—';
}

function MetricTile({
  label,
  value,
  hint,
}: {
  label: string;
  value: string | number;
  hint?: string;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-2xl tabular-nums">{value}</CardTitle>
      </CardHeader>
      {hint ? <CardContent className="text-muted-foreground pt-0 text-xs">{hint}</CardContent> : null}
    </Card>
  );
}

function statusColor(status: string) {
  switch (status) {
    case 'completed':
      return 'text-emerald-500';
    case 'running':
    case 'retrying':
      return 'text-sky-500';
    case 'failed':
      return 'text-red-500';
    case 'cancelled':
      return 'text-muted-foreground';
    default:
      return 'text-amber-500';
  }
}

export function InfrastructureDashboardPage() {
  const metrics = useInfrastructureMetricsQuery();
  const cache = useCacheStatsQuery();
  const queue = useQueueStatusQuery();
  const jobs = useJobsQuery();
  const submitJob = useSubmitJobMutation();
  const cancelJob = useCancelJobMutation();
  const retryJob = useRetryJobMutation();

  const m = metrics.data;

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h2 className="text-display text-2xl sm:text-[1.75rem]">Infrastructure</h2>
        <p className="text-muted-foreground text-sm">
          Enterprise analytics infrastructure — jobs, queue, cache, and system health.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricTile label="Queue depth" value={m?.queue_depth ?? '—'} hint="Jobs waiting" />
        <MetricTile label="Running" value={m?.jobs_running ?? '—'} />
        <MetricTile label="Queued" value={m?.jobs_queued ?? '—'} />
        <MetricTile
          label="Cache hit rate"
          value={
            m
              ? `${Math.round((m.cache_hits / Math.max(m.cache_hits + m.cache_misses, 1)) * 100)}%`
              : '—'
          }
          hint={`${m?.cache_keys ?? 0} keys`}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between gap-4">
            <div>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Activity className="size-4" />
                Job monitor
              </CardTitle>
              <CardDescription>Background analytics jobs for your organization</CardDescription>
            </div>
            <Button
              size="sm"
              disabled={submitJob.isPending}
              onClick={() =>
                submitJob.mutate({
                  job_type: 'data_intelligence',
                  name: `Profiling run ${new Date().toLocaleTimeString()}`,
                })
              }
            >
              Submit test job
            </Button>
          </CardHeader>
          <CardContent>
            <ul className="flex flex-col gap-3">
              {(jobs.data ?? []).slice(0, 12).map((job) => (
                <li
                  key={job.id}
                  className="border-border/60 flex flex-col gap-2 rounded-lg border p-3 text-sm"
                >
                  <div className="flex items-center justify-between gap-2">
                    <div>
                      <p className="font-medium">{job.name}</p>
                      <p className="text-muted-foreground text-xs">
                        {job.job_type} · {job.id.slice(0, 8)}
                      </p>
                    </div>
                    <span className={cn('text-xs font-medium capitalize', statusColor(job.status))}>
                      {job.status}
                    </span>
                  </div>
                  <div className="bg-muted h-1.5 overflow-hidden rounded-full">
                    <div
                      className="bg-primary h-full transition-all"
                      style={{ width: `${job.progress}%` }}
                    />
                  </div>
                  <div className="text-muted-foreground flex flex-wrap items-center gap-2 text-xs">
                    <span>{job.progress}%</span>
                    {job.duration_ms !== null && <span>· {job.duration_ms}ms</span>}
                    {job.retry_count > 0 && <span>· retries {job.retry_count}</span>}
                    {(job.status === 'queued' || job.status === 'running') && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="ml-auto h-7 px-2"
                        onClick={() => cancelJob.mutate(job.id)}
                      >
                        Cancel
                      </Button>
                    )}
                    {job.status === 'failed' && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="ml-auto h-7 px-2"
                        onClick={() => retryJob.mutate(job.id)}
                      >
                        Retry
                      </Button>
                    )}
                  </div>
                </li>
              ))}
              {jobs.isLoading && (
                <li className="text-muted-foreground text-sm">Loading jobs…</li>
              )}
              {!jobs.isLoading && (jobs.data ?? []).length === 0 && (
                <li className="text-muted-foreground text-sm">No background jobs yet.</li>
              )}
            </ul>
          </CardContent>
        </Card>

        <div className="flex flex-col gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Gauge className="size-4" />
                Performance
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm">
              <dl className="grid gap-2">
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Avg job duration</dt>
                  <dd className="tabular-nums">
                    {m?.avg_job_duration_ms != null
                      ? `${Math.round(m.avg_job_duration_ms)}ms`
                      : '—'}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Slow queries</dt>
                  <dd className="tabular-nums">{m?.slow_queries_detected ?? '—'}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Completed (24h)</dt>
                  <dd className="tabular-nums">{m?.jobs_completed_24h ?? '—'}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Failed (24h)</dt>
                  <dd className="tabular-nums">{m?.jobs_failed_24h ?? '—'}</dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Layers className="size-4" />
                Cache
              </CardTitle>
            </CardHeader>
            <CardContent className="text-muted-foreground text-sm">
              <p>Hits: {asMetric(cache.data?.hits)}</p>
              <p>Misses: {asMetric(cache.data?.misses)}</p>
              <p>Backend: {asMetric(cache.data?.backend)}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Server className="size-4" />
                Queue
              </CardTitle>
            </CardHeader>
            <CardContent className="text-muted-foreground text-sm">
              <p>Depth: {asMetric(queue.data?.queue_depth)}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Database className="size-4" />
                System health
              </CardTitle>
              <CardDescription>Use Overview for dependency probes</CardDescription>
            </CardHeader>
          </Card>
        </div>
      </div>
    </div>
  );
}
