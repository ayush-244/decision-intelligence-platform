import { cva, type VariantProps } from 'class-variance-authority';
import * as React from 'react';

import { cn } from '@/lib/utils';

/**
 * Status and evidence badges. `signal` is reserved for causal evidence and
 * citations; state colors follow the platform-wide semantic mapping
 * (emerald = success, sky = running, amber = pending/warning, red = failure).
 */
const badgeVariants = cva(
  'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium whitespace-nowrap',
  {
    variants: {
      variant: {
        default: 'border-border bg-muted text-muted-foreground',
        signal: 'border-primary/20 bg-primary/10 text-primary',
        success: 'border-emerald-500/20 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
        info: 'border-sky-500/20 bg-sky-500/10 text-sky-600 dark:text-sky-400',
        warning: 'border-amber-500/25 bg-amber-500/10 text-amber-600 dark:text-amber-400',
        destructive: 'border-red-500/20 bg-red-500/10 text-red-600 dark:text-red-400',
        outline: 'border-border text-foreground',
      },
    },
    defaultVariants: { variant: 'default' },
  },
);

function Badge({
  className,
  variant,
  ...props
}: React.ComponentProps<'span'> & VariantProps<typeof badgeVariants>) {
  return (
    <span data-slot="badge" className={cn(badgeVariants({ variant, className }))} {...props} />
  );
}

export { Badge, badgeVariants };
