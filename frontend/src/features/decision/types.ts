/** Decision intelligence API types. */

export interface DecisionRun {
  id: string;
  dataset_id: string;
  version_id: string;
  status: string;
  name: string;
  primary_objective: string;
  error_message?: string | null;
  executed_at?: string | null;
  created_at: string;
  result: DecisionResult;
}

export interface DecisionResult {
  recommendations: Recommendation[];
  rejected: Recommendation[];
  tradeoffs: Tradeoff[];
  priorities: Priority[];
  overall_summary: string;
  recommended_first: string | null;
  assumptions: string[];
  limitations: string[];
}

export interface Recommendation {
  rank: number;
  status: string;
  title: string;
  summary: string;
  reason: string;
  expected_outcome: number;
  confidence: number;
  roi: number;
  risk: number;
  business_explanation: string;
  implementation_difficulty: string;
  expected_timeline: string;
  validation_passed: boolean;
  decision_score: {
    overall_score: number;
    business_impact: number;
    roi: number;
    confidence: number;
    risk: number;
    methodology: string;
  };
  evidence: {
    causal_analysis_id: string;
    simulation_run_id: string;
    causal_summary: string;
    simulation_summary: string;
  };
}

export interface Tradeoff {
  dimension_a: string;
  dimension_b: string;
  option_a: string;
  option_b: string;
  tradeoff_summary: string;
  recommendation: string;
}

export interface Priority {
  simulation_run_id: string;
  title: string;
  priority_score: number;
  rank: number;
  factors: Array<[string, number, string]>;
}

export interface DecisionObjective {
  id: string;
  label: string;
}

export interface RunDecisionRequest {
  dataset_id: string;
  version_id?: string;
  name: string;
  primary_objective: string;
  simulation_run_ids?: string[];
  risk_tolerance?: number;
  min_confidence?: number;
  max_budget?: number;
}
