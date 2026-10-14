import { Link } from 'react-router-dom';

import { Button } from '@/components/ui/button';

export function NotFoundPage() {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-4 px-6 text-center">
      <p className="text-muted-foreground text-sm font-medium">404</p>
      <h1 className="text-display text-2xl sm:text-[1.75rem]">Page not found</h1>
      <p className="text-muted-foreground max-w-sm text-sm">
        The page you are looking for doesn’t exist or has moved.
      </p>
      <Button asChild>
        <Link to="/">Back home</Link>
      </Button>
    </div>
  );
}
