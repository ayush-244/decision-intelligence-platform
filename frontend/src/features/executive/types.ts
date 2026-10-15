/** Executive intelligence API types. */

export interface ExecutiveReport {
  id: string;
  dataset_id: string;
  version_id: string;
  decision_run_id?: string | null;
  status: string;
  name: string;
  business_objective: string;
  version_number: number;
  error_message?: string | null;
  executed_at?: string | null;
  created_at: string;
  result: ExecutiveReportResult;
}

export interface ExecutiveReportResult {
  executive_summary?: string;
  business_objective?: string;
  key_findings?: string[];
  decision_summary?: string;
  top_recommendations?: Array<Record<string, unknown>>;
  expected_roi?: Record<string, unknown>;
  expected_risks?: Record<string, unknown>;
  confidence_assessment?: {
    level?: string;
    score?: number;
    summary?: string;
  };
  key_assumptions?: string[];
  tradeoffs?: Array<Record<string, unknown>>;
  scenario_comparison?: Array<Record<string, unknown>>;
  implementation_roadmap?: TimelineItem[];
  business_kpis?: Array<Record<string, unknown>>;
  explainability?: ExplainabilityBlock[];
  narrative?: string;
  appendix?: Record<string, unknown>;
}

export interface ExplainabilityBlock {
  recommendation_title: string;
  why: string;
  evidence: {
    statistical?: string | null;
    causal: string;
    simulation: string;
    decision: string;
    confidence_level: string;
    confidence_score: number;
  };
  assumptions: string[];
  limitations: string[];
  business_interpretation: string;
  alternative_actions: string[];
}

export interface TimelineItem {
  priority: number;
  title: string;
  effort: string;
  impact: string;
  dependencies: string[];
  milestones: string[];
  timeline: string;
  business_owner: string;
  risk_level: string;
  expected_kpi_changes: string[];
}

export interface ExecutiveReportHistoryItem {
  id: string;
  name: string;
  status: string;
  version_number: number;
  created_at: string;
}

export interface ExecutiveDashboard {
  business_health_score: number;
  decision_pipeline: Record<string, number>;
  recommendation_status: Record<string, number>;
  roi_overview: Record<string, number>;
  risk_overview: Record<string, number>;
  confidence_overview: Record<string, number>;
  recent_decisions: Array<Record<string, unknown>>;
  historical_reports: number;
}

export interface GenerateReportRequest {
  dataset_id: string;
  version_id?: string;
  decision_run_id: string;
  name: string;
  business_objective: string;
  include_technical_appendix?: boolean;
}

export interface ExportReportResponse {
  content: string;
  media_type: string;
  filename: string;
}
