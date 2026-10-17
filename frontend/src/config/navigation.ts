import type { ComponentType } from 'react';
import {
  Bot,
  Database,
  FlaskConical,
  Gauge,
  GitBranch,
  LayoutDashboard,
  Lightbulb,
  Network,
  Sigma,
} from 'lucide-react';

export interface NavItem {
  label: string;
  to: string;
  icon: ComponentType<{ className?: string }>;
  /** Future modules are shown but disabled until their phase ships. */
  enabled: boolean;
  /**
   * Dataset-scoped stages route to the dataset list ("choose a dataset first").
   * Only the canonical owner of a path shows the active state.
   */
  canonical?: boolean;
  /** Reserved for RBAC / feature flags. */
  feature?: string;
}

export interface NavGroup {
  label: string;
  items: readonly NavItem[];
}

/**
 * Sidebar navigation, grouped by intent rather than feature list — mirroring
 * the analytical pipeline: Workspace (where work lives), Analyze (the
 * evidence pipeline), Decide (evidence into action), Operate (running it).
 */
export const APP_NAV_GROUPS: readonly NavGroup[] = [
  {
    label: 'Workspace',
    items: [
      {
        label: 'Overview',
        to: '/app/overview',
        icon: LayoutDashboard,
        enabled: true,
        feature: 'workspace',
      },
      {
        label: 'Datasets',
        to: '/app/datasets',
        icon: Database,
        enabled: true,
        feature: 'datasets',
      },
    ],
  },
  {
    label: 'Analyze',
    items: [
      {
        label: 'Statistics',
        to: '/app/datasets',
        icon: Sigma,
        enabled: true,
        canonical: false,
        feature: 'statistics',
      },
      {
        label: 'Causal Inference',
        to: '/app/datasets',
        icon: Network,
        enabled: true,
        canonical: false,
        feature: 'causal',
      },
      {
        label: 'Simulation',
        to: '/app/datasets',
        icon: FlaskConical,
        enabled: true,
        canonical: false,
        feature: 'simulation',
      },
    ],
  },
  {
    label: 'Decide',
    items: [
      {
        label: 'Recommendations',
        to: '/app/datasets',
        icon: Lightbulb,
        enabled: true,
        canonical: false,
        feature: 'recommendations',
      },
      {
        label: 'Reports',
        to: '/app/datasets',
        icon: GitBranch,
        enabled: true,
        canonical: false,
        feature: 'reports',
      },
      { label: 'AI Copilot', to: '/app/copilot', icon: Bot, enabled: true, feature: 'copilot' },
    ],
  },
  {
    label: 'Operate',
    items: [
      {
        label: 'Infrastructure',
        to: '/app/infrastructure',
        icon: Gauge,
        enabled: true,
        feature: 'infrastructure',
      },
    ],
  },
] as const;

/** Flat list retained for legacy consumers. */
export const APP_NAV_ITEMS: readonly NavItem[] = APP_NAV_GROUPS.flatMap((g) => g.items);
