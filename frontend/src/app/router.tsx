import { lazy, Suspense } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';

import { ProtectedRoute } from '@/app/routes/protected-route';
import { AppRouteFallback } from '@/app/routes/route-fallback';
import { AppLayout } from '@/layouts/app-layout';
import { MarketingLayout } from '@/layouts/marketing-layout';
import { LoginPage } from '@/pages/auth/login-page';
import { RegisterPage } from '@/pages/auth/register-page';
import { LandingPage } from '@/pages/landing/landing-page';
import { NotFoundPage } from '@/pages/not-found/not-found-page';

const DashboardPage = lazy(() =>
  import('@/pages/dashboard/dashboard-page').then((module) => ({
    default: module.DashboardPage,
  })),
);

const OrganizationSelectorPage = lazy(() =>
  import('@/pages/organizations/organization-selector-page').then((module) => ({
    default: module.OrganizationSelectorPage,
  })),
);

const WorkspaceDashboardPage = lazy(() =>
  import('@/pages/workspaces/workspace-dashboard-page').then((module) => ({
    default: module.WorkspaceDashboardPage,
  })),
);

const ProjectDashboardPage = lazy(() =>
  import('@/pages/projects/project-dashboard-page').then((module) => ({
    default: module.ProjectDashboardPage,
  })),
);

const DatasetListPage = lazy(() =>
  import('@/pages/datasets/dataset-list-page').then((module) => ({
    default: module.DatasetListPage,
  })),
);

const DatasetUploadPage = lazy(() =>
  import('@/pages/datasets/dataset-upload-page').then((module) => ({
    default: module.DatasetUploadPage,
  })),
);

const DatasetDetailPage = lazy(() =>
  import('@/pages/datasets/dataset-detail-page').then((module) => ({
    default: module.DatasetDetailPage,
  })),
);

const DatasetCausalPage = lazy(() =>
  import('@/pages/causal/dataset-causal-page').then((module) => ({
    default: module.DatasetCausalPage,
  })),
);

const DatasetSimulationPage = lazy(() =>
  import('@/pages/simulation/dataset-simulation-page').then((module) => ({
    default: module.DatasetSimulationPage,
  })),
);

const DatasetDecisionPage = lazy(() =>
  import('@/pages/decision/dataset-decision-page').then((module) => ({
    default: module.DatasetDecisionPage,
  })),
);

const DatasetStatisticsPage = lazy(() =>
  import('@/pages/statistics/dataset-statistics-page').then((module) => ({
    default: module.DatasetStatisticsPage,
  })),
);

const DecisionWorkspacePage = lazy(() =>
  import('@/pages/workspace/decision-workspace-page').then((module) => ({
    default: module.DecisionWorkspacePage,
  })),
);

const DatasetExecutivePage = lazy(() =>
  import('@/pages/executive/dataset-executive-page').then((module) => ({
    default: module.DatasetExecutivePage,
  })),
);

const DatasetIntelligencePage = lazy(() =>
  import('@/pages/intelligence/dataset-intelligence-page').then((module) => ({
    default: module.DatasetIntelligencePage,
  })),
);

const InfrastructureDashboardPage = lazy(() =>
  import('@/pages/infrastructure/infrastructure-dashboard-page').then((module) => ({
    default: module.InfrastructureDashboardPage,
  })),
);

const CopilotWorkspacePage = lazy(() =>
  import('@/pages/copilot/copilot-workspace-page').then((module) => ({
    default: module.CopilotWorkspacePage,
  })),
);

/** Application route table. App routes are lazy-loaded to keep the marketing bundle lean. */
export const router = createBrowserRouter([
  {
    path: '/',
    element: <MarketingLayout />,
    children: [
      { index: true, element: <LandingPage /> },
      { path: 'login', element: <LoginPage /> },
      { path: 'register', element: <RegisterPage /> },
    ],
  },
  {
    path: '/app',
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { index: true, element: <Navigate to="/app/organizations" replace /> },
          {
            path: 'organizations',
            element: (
              <Suspense fallback={<AppRouteFallback />}>
                <OrganizationSelectorPage />
              </Suspense>
            ),
          },
          {
            path: 'workspaces',
            element: (
              <Suspense fallback={<AppRouteFallback />}>
                <WorkspaceDashboardPage />
              </Suspense>
            ),
          },
          {
            path: 'workspaces/:workspaceId/projects',
            element: (
              <Suspense fallback={<AppRouteFallback />}>
                <ProjectDashboardPage />
              </Suspense>
            ),
          },
          {
            path: 'datasets',
            element: (
              <Suspense fallback={<AppRouteFallback />}>
                <DatasetListPage />
              </Suspense>
            ),
          },
          {
            path: 'datasets/upload',
            element: (
              <Suspense fallback={<AppRouteFallback />}>
                <DatasetUploadPage />
              </Suspense>
            ),
          },
          {
            path: 'workspace/:datasetId',
            element: (
              <Suspense fallback={<AppRouteFallback />}>
                <DecisionWorkspacePage />
              </Suspense>
            ),
          },
          {
            path: 'datasets/:datasetId/executive',
            element: (
              <Suspense fallback={<AppRouteFallback />}>
                <DatasetExecutivePage />
              </Suspense>
            ),
          },
          {
            path: 'datasets/:datasetId/decision',
            element: (
              <Suspense fallback={<AppRouteFallback />}>
                <DatasetDecisionPage />
              </Suspense>
            ),
          },
          {
            path: 'datasets/:datasetId/simulation',
            element: (
              <Suspense fallback={<AppRouteFallback />}>
                <DatasetSimulationPage />
              </Suspense>
            ),
          },
          {
            path: 'datasets/:datasetId/causal',
            element: (
              <Suspense fallback={<AppRouteFallback />}>
                <DatasetCausalPage />
              </Suspense>
            ),
          },
          {
            path: 'datasets/:datasetId/statistics',
            element: (
              <Suspense fallback={<AppRouteFallback />}>
                <DatasetStatisticsPage />
              </Suspense>
            ),
          },
          {
            path: 'datasets/:datasetId/intelligence',
            element: (
              <Suspense fallback={<AppRouteFallback />}>
                <DatasetIntelligencePage />
              </Suspense>
            ),
          },
          {
            path: 'datasets/:datasetId',
            element: (
              <Suspense fallback={<AppRouteFallback />}>
                <DatasetDetailPage />
              </Suspense>
            ),
          },
          {
            path: 'overview',
            element: (
              <Suspense fallback={<AppRouteFallback />}>
                <DashboardPage />
              </Suspense>
            ),
          },
          {
            path: 'infrastructure',
            element: (
              <Suspense fallback={<AppRouteFallback />}>
                <InfrastructureDashboardPage />
              </Suspense>
            ),
          },
          {
            path: 'copilot',
            element: (
              <Suspense fallback={<AppRouteFallback />}>
                <CopilotWorkspacePage />
              </Suspense>
            ),
          },
        ],
      },
    ],
  },
  { path: '*', element: <NotFoundPage /> },
]);
