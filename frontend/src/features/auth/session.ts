/** Client-side session persistence for access tokens and active organization. */

const ACCESS_TOKEN_KEY = 'delphi_access_token';
const ORGANIZATION_ID_KEY = 'delphi_organization_id';

export function getAccessToken(): string | null {
  return sessionStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setAccessToken(token: string): void {
  sessionStorage.setItem(ACCESS_TOKEN_KEY, token);
}

export function clearAccessToken(): void {
  sessionStorage.removeItem(ACCESS_TOKEN_KEY);
}

export function getActiveOrganizationId(): string | null {
  return sessionStorage.getItem(ORGANIZATION_ID_KEY);
}

export function setActiveOrganizationId(organizationId: string): void {
  sessionStorage.setItem(ORGANIZATION_ID_KEY, organizationId);
}

export function clearActiveOrganizationId(): void {
  sessionStorage.removeItem(ORGANIZATION_ID_KEY);
}

export function clearSession(): void {
  clearAccessToken();
  clearActiveOrganizationId();
}

export function isAuthenticated(): boolean {
  return getAccessToken() !== null;
}
