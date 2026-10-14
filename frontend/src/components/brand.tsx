import { cn } from '@/lib/utils';

/**
 * The Delphi mark: a minimal causal graph — cause flowing to effect — set in
 * the signal color, beside an editorial serif wordmark. Defined once and
 * reused across marketing and app chrome.
 */
export function Brand({ className }: { className?: string }) {
  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      <div className="bg-primary text-primary-foreground flex size-7 items-center justify-center rounded-md">
        <svg viewBox="0 0 24 24" className="size-4.5" fill="none" aria-hidden="true">
          {/* Directed causal path: X → M → Y */}
          <path
            d="M6.5 17L12 7.5M12 7.5L17.5 17M8 17h8"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            opacity="0.55"
          />
          <circle cx="12" cy="6.5" r="2.4" fill="currentColor" />
          <circle cx="5.5" cy="17.5" r="2.4" fill="currentColor" />
          <circle cx="18.5" cy="17.5" r="2.4" fill="currentColor" />
        </svg>
      </div>
      <span className="text-display text-lg leading-none">Delphi</span>
    </div>
  );
}
