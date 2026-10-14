/** Authentication and tenancy wire types (mirrors backend schemas). */

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  access_token_expires_in: number;
  token_type: string;
}

export interface AuthResult {
  user: User;
  tokens: AuthTokens;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  role: 'owner' | 'admin' | 'analyst' | 'viewer';
  created_at: string;
}

export interface Workspace {
  id: string;
  organization_id: string;
  name: string;
  slug: string;
  description: string | null;
  created_at: string;
}

export interface Project {
  id: string;
  workspace_id: string;
  name: string;
  slug: string;
  description: string | null;
  created_at: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface CreateOrganizationPayload {
  name: string;
}

export interface CreateWorkspacePayload {
  organization_id: string;
  name: string;
  description?: string;
}

export interface CreateProjectPayload {
  workspace_id: string;
  name: string;
  description?: string;
}
