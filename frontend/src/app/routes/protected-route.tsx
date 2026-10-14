import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { AppRouteFallback } from '@/app/routes/route-fallback';
import { getActiveOrganizationId, isAuthenticated } from '@/features/auth/session';
import { useSessionQuery } from '@/features/auth/hooks';

/**
 * Guards authenticated app routes. Redirects unauthenticated users to login and
 * routes users without an active organization to the org selector (except on that page).
 */
export function ProtectedRoute() {
  const location = useLocation();
  const session = useSessionQuery();

  if (!isAuthenticated()) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (session.isLoading) {
    return <AppRouteFallback />;
  }

  if (session.isError) {
    return <Navigate to="/login" replace />;
  }

  const onOrgSelector = location.pathname.startsWith('/app/organizations');
  if (!getActiveOrganizationId() && !onOrgSelector) {
    return <Navigate to="/app/organizations" replace />;
  }

  return <Outlet />;
}
