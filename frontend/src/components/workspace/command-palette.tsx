import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Command, Loader2, Search } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useWorkspaceSearchQuery } from '@/features/workspace';
import { cn } from '@/lib/utils';

interface CommandPaletteProps {
  datasetId?: string;
  projectId?: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandPalette({ datasetId, projectId, open, onOpenChange }: CommandPaletteProps) {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const search = useWorkspaceSearchQuery(query, datasetId);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        onOpenChange(!open);
      }
      if (event.key === 'Escape') onOpenChange(false);
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open, onOpenChange]);

  const quickActions = useMemo(
    () =>
      datasetId
        ? [
            { label: 'Open workspace', path: `/app/workspace/${datasetId}?project_id=${projectId ?? ''}` },
            { label: 'Data intelligence', path: `/app/datasets/${datasetId}/intelligence?project_id=${projectId ?? ''}` },
            { label: 'Causal analysis', path: `/app/datasets/${datasetId}/causal?project_id=${projectId ?? ''}` },
            { label: 'Simulation', path: `/app/datasets/${datasetId}/simulation?project_id=${projectId ?? ''}` },
            { label: 'Decisions', path: `/app/datasets/${datasetId}/decision?project_id=${projectId ?? ''}` },
            { label: 'Executive report', path: `/app/datasets/${datasetId}/executive?project_id=${projectId ?? ''}` },
          ]
        : [{ label: 'Browse datasets', path: '/app/datasets' }],
    [datasetId, projectId],
  );

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 p-4 pt-[12vh]">
      <button
        type="button"
        className="absolute inset-0"
        aria-label="Close command palette"
        onClick={() => onOpenChange(false)}
      />
      <div className="bg-background border-border relative w-full max-w-xl rounded-lg border shadow-2xl">
        <div className="flex items-center gap-2 border-b px-3">
          <Search className="text-muted-foreground size-4" />
          <Input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search projects, datasets, analyses, sessions…"
            className="border-0 shadow-none focus-visible:ring-0"
          />
          <kbd className="text-muted-foreground hidden rounded border px-1.5 py-0.5 text-[10px] sm:inline">
            Esc
          </kbd>
        </div>
        <div className="max-h-80 overflow-y-auto p-2">
          {query.length < 2 && (
            <div className="mb-2">
              <p className="text-muted-foreground px-2 py-1 text-xs font-medium uppercase">Quick actions</p>
              {quickActions.map((action) => (
                <button
                  key={action.path}
                  type="button"
                  className="hover:bg-muted flex w-full items-center gap-2 rounded-md px-2 py-2 text-left text-sm"
                  onClick={() => {
                    void navigate(action.path);
                    onOpenChange(false);
                  }}
                >
                  <Command className="size-3.5" />
                  {action.label}
                </button>
              ))}
            </div>
          )}
          {query.length >= 2 && search.isLoading && (
            <div className="text-muted-foreground flex items-center gap-2 p-4 text-sm">
              <Loader2 className="size-4 animate-spin" />
              Searching…
            </div>
          )}
          {query.length >= 2 &&
            search.data?.map((result) => (
              <button
                key={`${result.resource_type}-${result.resource_id}`}
                type="button"
                className="hover:bg-muted flex w-full flex-col rounded-md px-2 py-2 text-left"
                onClick={() => {
                  if (result.dataset_id) {
                    void navigate(`/app/workspace/${result.dataset_id}`);
                  }
                  onOpenChange(false);
                }}
              >
                <span className="text-sm font-medium">{result.title}</span>
                <span className="text-muted-foreground text-xs">
                  {result.resource_type}
                  {result.subtitle ? ` · ${result.subtitle}` : ''}
                </span>
              </button>
            ))}
        </div>
      </div>
    </div>
  );
}

interface GlobalSearchTriggerProps {
  onClick: () => void;
}

export function GlobalSearchTrigger({ onClick }: GlobalSearchTriggerProps) {
  return (
    <Button
      variant="outline"
      size="sm"
      className={cn(
        'text-muted-foreground hidden h-8 w-full max-w-xs justify-start gap-2 font-normal sm:flex',
      )}
      onClick={onClick}
    >
      <Search className="size-3.5" />
      <span className="flex-1 text-left">Search analyses, datasets, sessions…</span>
      <kbd>⌘K</kbd>
    </Button>
  );
}
