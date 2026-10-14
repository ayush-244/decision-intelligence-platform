import { Github } from 'lucide-react';
import { Link, Outlet } from 'react-router-dom';

import { Brand } from '@/components/brand';
import { ThemeToggle } from '@/components/theme-toggle';
import { Button } from '@/components/ui/button';

const GITHUB_URL = 'https://github.com/delphi-platform/delphi';

/** Chrome for public, unauthenticated pages (landing, marketing). */
export function MarketingLayout() {
  return (
    <div className="flex min-h-dvh flex-col">
      <header className="border-border/70 bg-background/85 sticky top-0 z-40 border-b backdrop-blur">
        <div className="mx-auto flex h-14 w-full max-w-6xl items-center justify-between px-6">
          <Link to="/" aria-label="Delphi home">
            <Brand />
          </Link>
          <nav className="flex items-center gap-1.5">
            <Button asChild size="icon" variant="ghost" aria-label="GitHub repository">
              <a href={GITHUB_URL} target="_blank" rel="noreferrer">
                <Github className="size-4" />
              </a>
            </Button>
            <ThemeToggle />
            <Button asChild size="sm" variant="ghost">
              <Link to="/login">Sign in</Link>
            </Button>
            <Button asChild size="sm">
              <Link to="/register">Get started</Link>
            </Button>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="border-border/70 border-t">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
          <div className="flex flex-col items-start justify-between gap-6 sm:flex-row sm:items-center">
            <Brand />
            <nav className="text-muted-foreground flex flex-wrap gap-x-6 gap-y-2 text-xs">
              <a className="hover:text-foreground transition-colors" href={GITHUB_URL} target="_blank" rel="noreferrer">
                GitHub
              </a>
              <a
                className="hover:text-foreground transition-colors"
                href={`${GITHUB_URL}/tree/main/docs`}
                target="_blank"
                rel="noreferrer"
              >
                Documentation
              </a>
              <a
                className="hover:text-foreground transition-colors"
                href={`${GITHUB_URL}/tree/main/examples`}
                target="_blank"
                rel="noreferrer"
              >
                Case studies
              </a>
              <Link className="hover:text-foreground transition-colors" to="/login">
                Sign in
              </Link>
            </nav>
          </div>
          <div className="text-muted-foreground flex flex-col items-start justify-between gap-2 text-xs sm:flex-row sm:items-center">
            <span>© {new Date().getFullYear()} Delphi · MIT licensed</span>
            <span className="font-display italic">Statistically rigorous. Transparent by design.</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
