import { ShieldX } from 'lucide-react';

import { Button } from '@/components/ui/button';

interface ForbiddenStateProps {
  title?: string;
  message?: string;
  onBack?: () => void;
}

export function ForbiddenState({
  title = 'Access denied',
  message = 'You do not have permission to view this resource.',
  onBack,
}: ForbiddenStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 px-6 py-16 text-center">
      <ShieldX className="text-muted-foreground size-10" />
      <h2 className="text-xl font-semibold">{title}</h2>
      <p className="text-muted-foreground max-w-md text-sm">{message}</p>
      {onBack ? (
        <Button variant="outline" onClick={onBack}>
          Go back
        </Button>
      ) : null}
    </div>
  );
}
