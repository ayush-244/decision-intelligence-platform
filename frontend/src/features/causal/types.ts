/** Causal inference API types. */

export interface DAGNode {
  id: string;
  label: string;
  role?: string;
  position?: { x: number; y: number };
}

export interface DAGEdge {
  source: string;
  target: string;
}

export interface DAGVersion {
  id: string;
  dataset_id: string;
  version_id: string;
  name: string;
  description?: string | null;
  nodes: DAGNode[];
  edges: DAGEdge[];
  variable_roles: Record<string, string>;
  version_number: number;
  is_valid: boolean;
  validation_errors: string[];
  created_at: string;
}

export interface CausalAnalysisRun {
  id: string;
  dataset_id: string;
  version_id: string;
  dag_version_id?: string | null;
  status: string;
  treatment: string;
  outcome: string;
  estimator?: string | null;
  error_message?: string | null;
  executed_at?: string | null;
  created_at: string;
  result: CausalAnalysisResult;
}

export interface CausalAnalysisResult {
  variable_roles: Array<{ name: string; role: string; confidence: number; reasoning: string }>;
  dag: { nodes: DAGNode[]; edges: DAGEdge[]; is_valid: boolean; validation_errors: string[] };
  assumption_report: {
    checks: Array<{ name: string; status: string; explanation: string }>;
    all_passed: boolean;
    required_assumptions: string[];
  };
  identification: {
    strategy: string;
    identified: boolean;
    adjustment_set: string[];
    reasoning: string;
    limitations: string[];
  };
  treatment_effect: {
    estimator: string;
    ate: number | null;
    att: number | null;
    atc: number | null;
    std_error: number | null;
    ci_lower: number | null;
    ci_upper: number | null;
    p_value: number | null;
  };
  refutation_results: Array<{
    method: string;
    original_effect: number;
    refuted_effect: number;
    passed: boolean;
    explanation: string;
  }>;
  sensitivity: {
    robustness_score: number;
    gamma_threshold: number | null;
    explanation: string;
    violations: string[];
  } | null;
  interpretation: {
    objective: string;
    business_interpretation: string;
    limitations: string[];
    recommended_next_steps: string[];
    causal_claim_valid: boolean;
  };
}

export interface CausalAnalyzeRequest {
  dataset_id: string;
  version_id?: string;
  dag_id?: string;
  treatment: string;
  outcome: string;
  business_question: string;
  estimator?: string;
  confidence_level?: number;
  run_refutation?: boolean;
  run_sensitivity?: boolean;
}
