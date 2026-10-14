import { AlertTriangle } from 'lucide-react';

import { Button } from '@/components/ui/button';
import type { ApiError } from '@/services/api/client';

interface ApiErrorStateProps {
  error: ApiError;
  onRetry?: () => void;
}

export function ApiErrorState({ error, onRetry }: ApiErrorStateProps) {
  return (
    <div className="border-destructive/30 bg-destructive/5 flex flex-col gap-3 rounded-lg border p-4">
      <div className="flex items-start gap-3">
        <AlertTriangle className="text-destructive mt-0.5 size-4 shrink-0" />
        <div className="text-sm">
          <p className="font-medium">{error.message}</p>
          {error.code ? (
            <p className="text-muted-foreground mt-1 text-xs">Code: {error.code}</p>
          ) : null}
          {error.requestId ? (
            <p className="text-muted-foreground text-xs">Request ID: {error.requestId}</p>
          ) : null}
        </div>
      </div>
      {onRetry ? (
        <Button size="sm" variant="outline" className="self-start" onClick={onRetry}>
          Retry
        </Button>
      ) : null}
    </div>
  );
}
