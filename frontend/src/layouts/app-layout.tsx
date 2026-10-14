import { Menu, X } from 'lucide-react';
import { useState } from 'react';
import { Link, NavLink, Outlet, useParams, useSearchParams } from 'react-router-dom';

import { Brand } from '@/components/brand';
import { CommandPalette, GlobalSearchTrigger } from '@/components/workspace/command-palette';
import { SystemStatus } from '@/components/system-status';
import { ThemeToggle } from '@/components/theme-toggle';
import { Button } from '@/components/ui/button';
import { APP_NAV_GROUPS, type NavItem } from '@/config/navigation';
import { cn } from '@/lib/utils';

function SidebarItem({ item, onNavigate }: { item: NavItem; onNavigate?: () => void }) {
  const Icon = item.icon;
  const base =
    'group relative flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-[13px] font-medium transition-colors duration-150';

  if (!item.enabled) {
    return (
      <span
        className={cn(base, 'text-muted-foreground/50 cursor-not-allowed')}
        aria-disabled="true"
        title="Coming soon"
      >
        <Icon className="size-4" />
        <span className="flex-1">{item.label}</span>
        <span className="bg-muted text-muted-foreground rounded px-1.5 py-0.5 text-[10px] tracking-wide uppercase">
          Soon
        </span>
      </span>
    );
  }

  // Dataset-scoped pipeline stages share a destination; only the canonical
  // owner of a path may show the active state.
  const canShowActive = item.canonical !== false;

  return (
    <NavLink
      to={item.to}
      end
      onClick={onNavigate}
      className={({ isActive }) =>
        cn(
          base,
          isActive && canShowActive
            ? 'bg-sidebar-accent text-sidebar-accent-foreground'
            : 'text-sidebar-foreground/65 hover:bg-sidebar-accent/60 hover:text-sidebar-foreground',
        )
      }
    >
      {({ isActive }) => {
        const active = isActive && canShowActive;
        return (
          <>
            {/* Signal rail — the vermilion mark of the active surface. */}
            <span
              aria-hidden
              className={cn(
                'bg-primary absolute top-1/2 left-0 h-4 w-0.5 -translate-y-1/2 rounded-full transition-opacity duration-150',
                active ? 'opacity-100' : 'opacity-0',
              )}
            />
            <Icon
              className={cn(
                'size-4 transition-colors',
                active
                  ? 'text-primary'
                  : 'text-sidebar-foreground/50 group-hover:text-sidebar-foreground/80',
              )}
            />
            {item.label}
          </>
        );
      }}
    </NavLink>
  );
}

function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="flex flex-1 flex-col gap-5 overflow-y-auto p-3">
      {APP_NAV_GROUPS.map((group) => (
        <div key={group.label} className="flex flex-col gap-0.5">
          <p className="text-sidebar-foreground/40 px-2.5 pb-1.5 text-[10px] font-semibold tracking-[0.14em] uppercase">
            {group.label}
          </p>
          {group.items.map((item) =>
            onNavigate ? (
              <SidebarItem key={item.label} item={item} onNavigate={onNavigate} />
            ) : (
              <SidebarItem key={item.label} item={item} />
            ),
          )}
        </div>
      ))}
    </nav>
  );
}

/**
 * Authenticated application shell.
 *
 * Layout grammar: a quiet sidebar organized by intent (Workspace → Analyze →
 * Decide → Operate) mirroring the analytical pipeline, a hairline header with
 * global search as the centerpiece (⌘K), and a content plane that pages own
 * entirely. Navigation should feel invisible; the signal rail always shows
 * where you are.
 */
export function AppLayout() {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const { datasetId } = useParams<{ datasetId?: string }>();
  const [searchParams] = useSearchParams();
  const projectId = searchParams.get('project_id') ?? undefined;

  return (
    <div className="bg-background flex min-h-dvh">
      <aside className="bg-sidebar border-sidebar-border hidden w-60 shrink-0 flex-col border-r md:flex">
        <div className="border-sidebar-border flex h-14 items-center border-b px-4">
          <Link to="/" aria-label="Delphi home">
            <Brand />
          </Link>
        </div>
        <SidebarNav />
        <div className="border-sidebar-border border-t p-4">
          <SystemStatus />
        </div>
      </aside>

      {mobileNavOpen ? (
        <div className="fixed inset-0 z-50 md:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            aria-label="Close navigation"
            onClick={() => setMobileNavOpen(false)}
          />
          <aside className="bg-sidebar border-sidebar-border relative flex h-full w-72 max-w-[85vw] flex-col border-r shadow-xl">
            <div className="border-sidebar-border flex h-14 items-center justify-between border-b px-4">
              <Link to="/" aria-label="Delphi home" onClick={() => setMobileNavOpen(false)}>
                <Brand />
              </Link>
              <Button variant="ghost" size="icon" onClick={() => setMobileNavOpen(false)}>
                <X className="size-4" />
              </Button>
            </div>
            <SidebarNav onNavigate={() => setMobileNavOpen(false)} />
            <div className="border-sidebar-border mt-auto border-t p-4">
              <SystemStatus />
            </div>
          </aside>
        </div>
      ) : null}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="border-border/70 bg-background/85 sticky top-0 z-30 flex h-14 items-center justify-between gap-3 border-b px-4 backdrop-blur sm:px-6">
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            aria-label="Open navigation"
            onClick={() => setMobileNavOpen(true)}
          >
            <Menu className="size-4" />
          </Button>
          <GlobalSearchTrigger onClick={() => setCommandOpen(true)} />
          <ThemeToggle />
        </header>
        <main className="flex-1 p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
      <CommandPalette
        open={commandOpen}
        onOpenChange={setCommandOpen}
        {...(datasetId ? { datasetId } : {})}
        {...(projectId ? { projectId } : {})}
      />
    </div>
  );
}
