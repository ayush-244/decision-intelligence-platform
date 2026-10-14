import type { ComponentType, ReactNode } from 'react';

import { cn } from '@/lib/utils';

/**
 * Standard empty surface on the plotting-paper motif. Every list, panel, and
 * workspace uses this instead of a blank div, so "nothing yet" still looks
 * deliberate and tells the user what to do next.
 */
export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: {
  icon?: ComponentType<{ className?: string }>;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        'border-border/80 bg-plot-grid relative flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed px-6 py-12 text-center',
        className,
      )}
    >
      <div className="from-background/40 to-background/90 pointer-events-none absolute inset-0 rounded-lg bg-gradient-to-b" />
      <div className="relative flex flex-col items-center gap-2">
        {Icon ? (
          <div className="border-border bg-card text-muted-foreground mb-1 flex size-10 items-center justify-center rounded-md border shadow-xs">
            <Icon className="size-4.5" />
          </div>
        ) : null}
        <p className="text-sm font-semibold">{title}</p>
        {description ? (
          <p className="text-muted-foreground max-w-sm text-sm text-balance">{description}</p>
        ) : null}
        {action ? <div className="mt-3">{action}</div> : null}
      </div>
    </div>
  );
}
