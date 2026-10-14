import type { HealthStatus } from '@/features/system';
import { useHealthQuery } from '@/features/system';
import { cn } from '@/lib/utils';

interface StatusStyle {
  dot: string;
  label: string;
}

const UNKNOWN_STYLE: StatusStyle = { dot: 'bg-muted-foreground', label: 'Checking status…' };

const STATUS_STYLES = {
  healthy: { dot: 'bg-emerald-500', label: 'All systems operational' },
  degraded: { dot: 'bg-amber-500', label: 'Degraded performance' },
  unhealthy: { dot: 'bg-red-500', label: 'Service disruption' },
} satisfies Record<HealthStatus, StatusStyle>;

/**
 * Live backend status pill. Demonstrates the end-to-end data path
 * (TanStack Query -> typed API client -> FastAPI readiness endpoint) without
 * introducing any business logic.
 */
export function SystemStatus({ className }: { className?: string }) {
  const { data, isError } = useHealthQuery();
  const style: StatusStyle = isError
    ? STATUS_STYLES.unhealthy
    : data
      ? STATUS_STYLES[data.status]
      : UNKNOWN_STYLE;

  return (
    <div
      className={cn(
        'text-muted-foreground inline-flex items-center gap-2 text-xs font-medium',
        className,
      )}
    >
      <span className="relative flex size-2">
        <span className={cn('absolute inline-flex size-2 rounded-full', style.dot)} />
      </span>
      {style.label}
    </div>
  );
}
