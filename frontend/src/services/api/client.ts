import { env } from '@/config/env';
import { getAccessToken, setAccessToken, clearSession } from '@/features/auth/session';
import type { AuthResult } from '@/features/auth/types';
import { toast } from 'sonner';

/** Error thrown for non-2xx API responses, carrying the parsed envelope. */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly code?: string,
    public readonly requestId?: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

interface BackendErrorEnvelope {
  error?: { code?: string; message?: string; request_id?: string };
}

interface DataEnvelope<T> {
  data: T;
}

const REQUEST_ID_HEADER = 'X-Request-ID';

function createRequestId(): string {
  return crypto.randomUUID();
}

function buildHeaders(init?: RequestInit): HeadersInit {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    [REQUEST_ID_HEADER]: createRequestId(),
  };
  const token = getAccessToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  if (init?.headers) {
    Object.assign(headers, init.headers);
  }
  return headers;
}

async function parseError(response: Response, requestId: string): Promise<ApiError> {
  let code: string | undefined;
  let requestIdFromServer: string | undefined;
  let message = `Request failed with status ${response.status}`;
  try {
    const body = (await response.json()) as BackendErrorEnvelope;
    code = body.error?.code;
    requestIdFromServer =
      body.error?.request_id ?? response.headers.get(REQUEST_ID_HEADER) ?? undefined;
    message = body.error?.message ?? message;
  } catch {
    requestIdFromServer = response.headers.get(REQUEST_ID_HEADER) ?? undefined;
  }
  return new ApiError(response.status, message, code, requestIdFromServer ?? requestId);
}

async function tryRefreshSession(): Promise<boolean> {
  const response = await fetch(`${env.apiBaseUrl}/api/v1/auth/refresh`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      [REQUEST_ID_HEADER]: createRequestId(),
    },
  });
  if (!response.ok) {
    return false;
  }
  const body = (await response.json()) as DataEnvelope<AuthResult>;
  setAccessToken(body.data.tokens.access_token);
  return true;
}

/**
 * Thin, typed wrapper around `fetch`.
 *
 * Responsibilities: prefix the configured base URL, propagate correlation IDs,
 * include credentials for cookie-based refresh tokens, parse JSON, and normalise
 * backend error envelopes into a typed {@link ApiError}.
 */
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const requestId = createRequestId();
  const doFetch = () =>
    fetch(`${env.apiBaseUrl}${path}`, {
      credentials: 'include',
      ...init,
      headers: buildHeaders(init),
    });

  let response = await doFetch();

  if (response.status === 401 && !path.endsWith('/auth/refresh') && getAccessToken()) {
    const refreshed = await tryRefreshSession();
    if (refreshed) {
      response = await doFetch();
    } else {
      clearSession();
      toast.error('Session expired. Please sign in again.');
    }
  }

  if (!response.ok) {
    const apiError = await parseError(response, requestId);
    if (apiError.status === 403) {
      toast.error(apiError.message);
    }
    throw apiError;
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

/** Unwrap `{ "data": T }` success envelopes from the backend. */
export async function apiFetchData<T>(path: string, init?: RequestInit): Promise<T> {
  const envelope = await apiFetch<DataEnvelope<T>>(path, init);
  return envelope.data;
}
