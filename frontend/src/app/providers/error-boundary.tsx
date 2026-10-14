import { Component, type ErrorInfo, type ReactNode } from 'react';

import { Button } from '@/components/ui/button';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

/**
 * Catches render errors so a single feature failure does not white-screen the SPA.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('Unhandled UI error', error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="bg-background flex min-h-dvh flex-col items-center justify-center gap-4 px-6 text-center">
          <p className="text-muted-foreground text-sm font-medium">Something went wrong</p>
          <h1 className="text-2xl font-semibold tracking-tight">Unexpected application error</h1>
          <p className="text-muted-foreground max-w-md text-sm">
            Try reloading the page. If the problem persists, contact your administrator with the
            time this occurred.
          </p>
          <Button onClick={() => window.location.reload()}>Reload</Button>
        </div>
      );
    }

    return this.props.children;
  }
}
