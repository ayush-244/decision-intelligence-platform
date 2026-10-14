/**
 * Validated, typed access to runtime environment configuration.
 *
 * Centralising env access (rather than reading `import.meta.env` throughout the
 * app) gives us one place to validate, default, and document configuration —
 * and one place to change if the source ever moves.
 */

interface AppEnv {
  readonly apiBaseUrl: string;
  readonly appName: string;
}

function required(value: string | undefined, key: string, fallback: string): string {
  if (value === undefined || value === '') {
    if (import.meta.env.PROD) {
      // Fail loudly in production builds rather than shipping a broken client.
      throw new Error(`Missing required environment variable: ${key}`);
    }
    return fallback;
  }
  return value;
}

export const env: AppEnv = {
  apiBaseUrl: required(
    import.meta.env.VITE_API_BASE_URL,
    'VITE_API_BASE_URL',
    'http://localhost:8000',
  ),
  appName: required(import.meta.env.VITE_APP_NAME, 'VITE_APP_NAME', 'Delphi'),
};
