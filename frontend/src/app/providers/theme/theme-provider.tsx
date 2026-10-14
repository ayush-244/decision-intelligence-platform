import { useCallback, useEffect, useMemo, useState } from 'react';

import { registerChartTheme } from '@/lib/chart-theme';

import { THEME_STORAGE_KEY, ThemeContext, type Theme, type ThemeContextValue } from './theme';

interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: Theme;
}

function getSystemTheme(): 'light' | 'dark' {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function readStoredTheme(fallback: Theme): Theme {
  const stored = localStorage.getItem(THEME_STORAGE_KEY);
  return stored === 'light' || stored === 'dark' || stored === 'system' ? stored : fallback;
}

/**
 * Provides theme state, persists the user's choice, and keeps the `dark` class
 * on <html> in sync — including live updates when the OS theme changes and the
 * user has selected `system`.
 */
export function ThemeProvider({ children, defaultTheme = 'dark' }: ThemeProviderProps) {
  const [theme, setThemeState] = useState<Theme>(() => readStoredTheme(defaultTheme));
  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>(() =>
    theme === 'system' ? getSystemTheme() : theme,
  );

  useEffect(() => {
    const root = window.document.documentElement;
    const effective = theme === 'system' ? getSystemTheme() : theme;
    setResolvedTheme(effective);
    root.classList.toggle('dark', effective === 'dark');
    // Charts read design tokens at registration; refresh on theme change.
    registerChartTheme();
  }, [theme]);

  useEffect(() => {
    if (theme !== 'system') return;
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const onChange = () => {
      const effective = getSystemTheme();
      setResolvedTheme(effective);
      window.document.documentElement.classList.toggle('dark', effective === 'dark');
    };
    media.addEventListener('change', onChange);
    return () => media.removeEventListener('change', onChange);
  }, [theme]);

  const setTheme = useCallback((next: Theme) => {
    localStorage.setItem(THEME_STORAGE_KEY, next);
    setThemeState(next);
  }, []);

  const value = useMemo<ThemeContextValue>(
    () => ({ theme, resolvedTheme, setTheme }),
    [theme, resolvedTheme, setTheme],
  );

  return <ThemeContext value={value}>{children}</ThemeContext>;
}
