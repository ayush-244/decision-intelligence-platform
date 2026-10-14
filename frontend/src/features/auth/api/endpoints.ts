import {
  clearSession,
  getAccessToken,
  getActiveOrganizationId,
  setAccessToken,
  setActiveOrganizationId,
} from '@/features/auth/session';
import type {
  AuthResult,
  CreateOrganizationPayload,
  CreateProjectPayload,
  CreateWorkspacePayload,
  LoginPayload,
  Organization,
  Project,
  RegisterPayload,
  User,
  Workspace,
} from '@/features/auth/types';
import { apiFetch, apiFetchData } from '@/services/api/client';

export function registerUser(payload: RegisterPayload): Promise<User> {
  return apiFetchData<User>('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function loginUser(payload: LoginPayload): Promise<AuthResult> {
  return apiFetchData<AuthResult>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function refreshSession(): Promise<AuthResult> {
  const result = await apiFetchData<AuthResult>('/api/v1/auth/refresh', { method: 'POST' });
  setAccessToken(result.tokens.access_token);
  return result;
}

export async function logoutUser(): Promise<void> {
  const token = getAccessToken();
  const init: RequestInit = { method: 'POST' };
  if (token) {
    init.headers = { Authorization: `Bearer ${token}` };
  }
  await apiFetch('/api/v1/auth/logout', init);
  clearSession();
}

export function fetchCurrentUser(): Promise<User> {
  return apiFetchData<User>('/api/v1/auth/me');
}

export function fetchOrganizations(): Promise<Organization[]> {
  return apiFetchData<Organization[]>('/api/v1/organizations');
}

export function createOrganization(payload: CreateOrganizationPayload): Promise<Organization> {
  return apiFetchData<Organization>('/api/v1/organizations', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function fetchWorkspaces(): Promise<Workspace[]> {
  const organizationId = getActiveOrganizationId();
  if (!organizationId) {
    return Promise.reject(new Error('No active organization selected.'));
  }
  return apiFetchData<Workspace[]>('/api/v1/workspaces', {
    headers: { 'X-Organization-ID': organizationId },
  });
}

export function createWorkspace(payload: CreateWorkspacePayload): Promise<Workspace> {
  const organizationId = getActiveOrganizationId();
  if (!organizationId) {
    return Promise.reject(new Error('No active organization selected.'));
  }
  return apiFetchData<Workspace>('/api/v1/workspaces', {
    method: 'POST',
    body: JSON.stringify(payload),
    headers: { 'X-Organization-ID': organizationId },
  });
}

export function fetchProjects(workspaceId: string): Promise<Project[]> {
  const organizationId = getActiveOrganizationId();
  if (!organizationId) {
    return Promise.reject(new Error('No active organization selected.'));
  }
  return apiFetchData<Project[]>(`/api/v1/projects?workspace_id=${workspaceId}`, {
    headers: { 'X-Organization-ID': organizationId },
  });
}

export function createProject(payload: CreateProjectPayload): Promise<Project> {
  const organizationId = getActiveOrganizationId();
  if (!organizationId) {
    return Promise.reject(new Error('No active organization selected.'));
  }
  return apiFetchData<Project>('/api/v1/projects', {
    method: 'POST',
    body: JSON.stringify(payload),
    headers: { 'X-Organization-ID': organizationId },
  });
}

export function persistAuthResult(result: AuthResult): void {
  setAccessToken(result.tokens.access_token);
}

export function persistOrganizationSelection(organizationId: string): void {
  setActiveOrganizationId(organizationId);
}
