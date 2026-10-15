/** Unified decision workspace types. */

export type WorkflowStep =
  | 'select_project'
  | 'select_version'
  | 'data_intelligence'
  | 'statistical_analysis'
  | 'review_assumptions'
  | 'causal_dag'
  | 'causal_analysis'
  | 'simulation'
  | 'recommendations'
  | 'executive_report'
  | 'save_session';

export interface WorkflowProgress {
  current_step: WorkflowStep;
  completed_steps: WorkflowStep[];
  total_steps: number;
  percent_complete: number;
  next_step: WorkflowStep | null;
}

export interface DecisionSession {
  id: string;
  dataset_id: string;
  version_id: string;
  name: string;
  description?: string | null;
  status: string;
  version_number: number;
  current_step: WorkflowStep;
  workspace_state: WorkspaceState;
  progress?: WorkflowProgress;
  created_at: string;
}

export interface WorkspaceState {
  panels: {
    sidebar: boolean;
    context: boolean;
    timeline: boolean;
    evidence: boolean;
  };
  canvas: {
    nodes: CanvasNode[];
    active_node: string | null;
  };
  comparison: string | null;
}

export interface CanvasNode {
  id: string;
  type: string;
  title: string;
  status: 'pending' | 'active' | 'completed';
  href?: string;
}

export interface SessionHistoryItem {
  id: string;
  name: string;
  status: string;
  version_number: number;
  current_step: string;
  created_at: string;
}

export interface TimelineEvent {
  id: string;
  event_type: string;
  title: string;
  description?: string | null;
  resource_type?: string | null;
  resource_id?: string | null;
  occurred_at: string;
}

export interface SearchResult {
  resource_type: string;
  resource_id: string;
  title: string;
  subtitle?: string | null;
  dataset_id?: string | null;
  created_at?: string | null;
}

export interface SessionComparison {
  session_a_id: string;
  session_b_id: string;
  items: Array<{
    label: string;
    value_a: unknown;
    value_b: unknown;
    delta: unknown;
    highlight: boolean;
  }>;
  summary: string;
}

export const WORKFLOW_STEPS: Array<{ id: WorkflowStep; label: string }> = [
  { id: 'select_version', label: 'Dataset version' },
  { id: 'data_intelligence', label: 'Data intelligence' },
  { id: 'statistical_analysis', label: 'Statistics' },
  { id: 'review_assumptions', label: 'Assumptions' },
  { id: 'causal_dag', label: 'Causal DAG' },
  { id: 'causal_analysis', label: 'Causal analysis' },
  { id: 'simulation', label: 'Simulation' },
  { id: 'recommendations', label: 'Recommendations' },
  { id: 'executive_report', label: 'Executive report' },
  { id: 'save_session', label: 'Save session' },
];
