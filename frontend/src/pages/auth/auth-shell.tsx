import type { ReactNode } from 'react';
import { CheckCircle2 } from 'lucide-react';

/**
 * Two-panel editorial auth layout. The form sits on the paper plane; the
 * companion panel restates the product promise on the plotting-paper motif —
 * a first impression of the design language before users ever sign in.
 */
export function AuthShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <div className="mx-auto grid w-full max-w-5xl gap-10 px-6 py-16 lg:grid-cols-[1fr_420px] lg:gap-16 lg:py-24">
      <div className="bg-plot-grid relative hidden overflow-hidden rounded-xl border lg:block">
        <div className="from-background/20 via-background/60 to-background/95 pointer-events-none absolute inset-0 bg-gradient-to-b" />
        <div className="relative flex h-full flex-col justify-end gap-6 p-10">
          <p className="text-display text-3xl leading-snug text-balance">
            Dashboards describe.
            <br />
            <span className="text-primary italic">Delphi explains.</span>
          </p>
          <ul className="text-muted-foreground space-y-2.5 text-sm">
            {[
              'Causal effects, not correlations',
              'Counterfactual simulation before you commit',
              'Recommendations with assumptions stated',
              'AI that cites evidence — never invents it',
            ].map((line) => (
              <li key={line} className="flex items-start gap-2">
                <CheckCircle2 className="text-primary mt-0.5 size-4 shrink-0" />
                {line}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="flex flex-col justify-center">
        <div className="mb-8 flex flex-col gap-1.5">
          <h1 className="text-display text-3xl tracking-tight">{title}</h1>
          <p className="text-muted-foreground text-sm">{subtitle}</p>
        </div>
        {children}
      </div>
    </div>
  );
}
