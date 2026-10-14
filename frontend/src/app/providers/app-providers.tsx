import { QueryProvider } from './query-provider';
import { ThemeProvider } from './theme/theme-provider';
import { Toaster } from 'sonner';

/**
 * Single composition point for global providers. Order matters: theme is
 * outermost so every child (including any error UI) is themed correctly.
 */
export function AppProviders({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider defaultTheme="dark">
      <QueryProvider>
        {children}
        <Toaster richColors closeButton position="top-right" />
      </QueryProvider>
    </ThemeProvider>
  );
}
