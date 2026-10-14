import { Moon, Sun } from 'lucide-react';

import { useTheme } from '@/app/providers/theme/theme';
import { Button } from '@/components/ui/button';

/** Toggles between light and dark, respecting the currently resolved theme. */
export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const isDark = resolvedTheme === 'dark';

  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
    >
      {isDark ? <Sun className="size-4" /> : <Moon className="size-4" />}
    </Button>
  );
}
