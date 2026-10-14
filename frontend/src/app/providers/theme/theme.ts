import { createContext, useContext } from 'react';

/** Supported colour-scheme preferences. `system` follows the OS setting. */
export type Theme = 'light' | 'dark' | 'system';

export interface ThemeContextValue {
  theme: Theme;
  /** The effective theme after resolving `system`. */
  resolvedTheme: 'light' | 'dark';
  setTheme: (theme: Theme) => void;
}

export const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

/** Access the current theme. Must be used within a `ThemeProvider`. */
export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

export const THEME_STORAGE_KEY = 'delphi-theme';
