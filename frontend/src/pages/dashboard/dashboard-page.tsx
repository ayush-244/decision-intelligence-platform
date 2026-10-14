import { CheckCircle2, Circle } from 'lucide-react';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useHealthQuery, useVersionQuery } from '@/features/system';
import { cn } from '@/lib/utils';

const ROADMAP = [
  { label: 'Engineering foundation', done: true },
  { label: 'Authentication & workspaces', done: false },
  { label: 'Dataset upload & profiling', done: false },
  { label: 'Statistical analysis & EDA', done: false },
  { label: 'Causal inference engine', done: false },
  { label: 'Counterfactual simulation', done: false },
  { label: 'Recommendation engine', done: false },
] as const;

export function DashboardPage() {
  const version = useVersionQuery();
  const health = useHealthQuery();

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
      <div>
        <h2 className="text-display text-2xl sm:text-[1.75rem]">Overview</h2>
        <p className="text-muted-foreground mt-1 text-sm">
          Foundation is live. Analytical modules arrive in upcoming phases.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardDescription>Service</CardDescription>
            <CardTitle className="text-lg">
              {version.data?.name ?? 'Delphi'}
              <span className="text-muted-foreground ml-2 text-sm font-normal">
                v{version.data?.version ?? '—'}
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="text-muted-foreground text-sm">
            Environment: {version.data?.environment ?? '—'}
          </CardContent>
        </Card>

        <Card className="sm:col-span-2">
          <CardHeader>
            <CardDescription>Dependencies</CardDescription>
            <CardTitle className="text-lg capitalize">
              {health.isLoading ? 'Checking…' : (health.data?.status ?? 'Unavailable')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="flex flex-col gap-2">
              {(health.data?.components ?? []).map((component) => (
                <li key={component.name} className="flex items-center justify-between text-sm">
                  <span className="capitalize">{component.name}</span>
                  <span
                    className={cn(
                      'inline-flex items-center gap-1.5 text-xs font-medium',
                      component.status === 'healthy'
                        ? 'text-emerald-500'
                        : component.status === 'degraded'
                          ? 'text-amber-500'
                          : 'text-red-500',
                    )}
                  >
                    <span className="size-1.5 rounded-full bg-current" />
                    {component.status}
                    {component.latency_ms !== null && (
                      <span className="text-muted-foreground">· {component.latency_ms}ms</span>
                    )}
                  </span>
                </li>
              ))}
              {health.isError && (
                <li className="text-muted-foreground text-sm">
                  Backend unreachable. Start it with <code>make dev-backend</code> or{' '}
                  <code>docker compose up</code>.
                </li>
              )}
            </ul>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Roadmap</CardTitle>
          <CardDescription>What ships next, in order.</CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="flex flex-col gap-3">
            {ROADMAP.map((item) => (
              <li key={item.label} className="flex items-center gap-3 text-sm">
                {item.done ? (
                  <CheckCircle2 className="size-4 text-emerald-500" />
                ) : (
                  <Circle className="text-muted-foreground/40 size-4" />
                )}
                <span className={cn(!item.done && 'text-muted-foreground')}>{item.label}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
