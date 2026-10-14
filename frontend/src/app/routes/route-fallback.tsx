/**
 * Branded suspense fallback for lazy-loaded routes: the Delphi mark pulsing on
 * the plotting-paper canvas. Communicates "the instrument is warming up"
 * rather than a generic spinner.
 */
export function AppRouteFallback() {
  return (
    <div className="bg-plot-grid relative flex min-h-[50vh] items-center justify-center rounded-lg">
      <div className="from-background/30 to-background/80 pointer-events-none absolute inset-0 bg-gradient-to-b" />
      <div className="relative flex flex-col items-center gap-3">
        <div className="bg-primary text-primary-foreground flex size-9 animate-pulse items-center justify-center rounded-md">
          <svg viewBox="0 0 24 24" className="size-5" fill="none" aria-hidden="true">
            <path
              d="M12 3l7 4v6c0 4-3 6-7 8-4-2-7-4-7-8V7l7-4z"
              stroke="currentColor"
              strokeWidth="1.75"
              strokeLinejoin="round"
            />
            <path
              d="M9 12l2 2 4-4"
              stroke="currentColor"
              strokeWidth="1.75"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <p className="text-muted-foreground text-xs font-medium tracking-wide">Loading workspace…</p>
      </div>
    </div>
  );
}
