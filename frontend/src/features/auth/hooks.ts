import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  createOrganization,
  createProject,
  createWorkspace,
  fetchCurrentUser,
  fetchOrganizations,
  fetchProjects,
  fetchWorkspaces,
  loginUser,
  logoutUser,
  persistAuthResult,
  persistOrganizationSelection,
  refreshSession,
  registerUser,
} from '@/features/auth/api/endpoints';
import { getAccessToken, getActiveOrganizationId, isAuthenticated } from '@/features/auth/session';
import type {
  CreateOrganizationPayload,
  CreateProjectPayload,
  CreateWorkspacePayload,
  LoginPayload,
  RegisterPayload,
} from '@/features/auth/types';

export const authKeys = {
  session: ['auth', 'session'] as const,
  organizations: ['auth', 'organizations'] as const,
  workspaces: ['auth', 'workspaces'] as const,
  projects: (workspaceId: string) => ['auth', 'projects', workspaceId] as const,
};

export function useSessionQuery() {
  return useQuery({
    queryKey: authKeys.session,
    queryFn: fetchCurrentUser,
    enabled: isAuthenticated(),
    retry: false,
  });
}

export function useLoginMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: LoginPayload) => {
      const result = await loginUser(payload);
      persistAuthResult(result);
      return result;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: authKeys.session });
    },
  });
}

export function useRegisterMutation() {
  return useMutation({
    mutationFn: (payload: RegisterPayload) => registerUser(payload),
  });
}

export function useLogoutMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: logoutUser,
    onSettled: () => {
      queryClient.clear();
    },
  });
}

export function useRefreshSessionMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: refreshSession,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: authKeys.session });
    },
  });
}

export function useOrganizationsQuery() {
  return useQuery({
    queryKey: authKeys.organizations,
    queryFn: fetchOrganizations,
    enabled: getAccessToken() !== null,
  });
}

export function useCreateOrganizationMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateOrganizationPayload) => createOrganization(payload),
    onSuccess: (organization) => {
      persistOrganizationSelection(organization.id);
      void queryClient.invalidateQueries({ queryKey: authKeys.organizations });
    },
  });
}

export function useWorkspacesQuery() {
  return useQuery({
    queryKey: authKeys.workspaces,
    queryFn: fetchWorkspaces,
    enabled: getAccessToken() !== null && getActiveOrganizationId() !== null,
  });
}

export function useCreateWorkspaceMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateWorkspacePayload) => createWorkspace(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: authKeys.workspaces });
    },
  });
}

export function useProjectsQuery(workspaceId: string | undefined) {
  return useQuery({
    queryKey: authKeys.projects(workspaceId ?? 'none'),
    queryFn: () => fetchProjects(workspaceId!),
    enabled: Boolean(workspaceId && getAccessToken()),
  });
}

export function useCreateProjectMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateProjectPayload) => createProject(payload),
    onSuccess: (_project, variables) => {
      void queryClient.invalidateQueries({
        queryKey: authKeys.projects(variables.workspace_id),
      });
    },
  });
}

export { persistOrganizationSelection };
