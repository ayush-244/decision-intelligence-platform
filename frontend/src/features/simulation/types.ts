/** Simulation engine API types. */

export interface Intervention {
  variable: string;
  mode: 'absolute' | 'relative' | 'set_value' | 'toggle';
  value: number | string | boolean;
  reason?: string;
}

export interface Constraint {
  type: string;
  severity: 'hard' | 'soft';
  threshold?: number | null;
  description: string;
  value?: number | null;
}

export interface SimulationScenario {
  id: string;
  dataset_id: string;
  version_id: string;
  name: string;
  description?: string | null;
  objective?: string | null;
  notes?: string | null;
  is_baseline: boolean;
  interventions: Intervention[];
  constraints: Constraint[];
  version_number: number;
  parent_scenario_id?: string | null;
  created_at: string;
}

export interface SimulationRun {
  id: string;
  dataset_id: string;
  version_id: string;
  causal_analysis_id: string;
  statistical_analysis_id?: string | null;
  scenario_id: string;
  status: string;
  name: string;
  error_message?: string | null;
  executed_at?: string | null;
  created_at: string;
  result: SimulationResult;
}

export interface SimulationResult {
  counterfactual: {
    baseline_outcome: number;
    expected_outcome: number;
    expected_treatment_effect: number;
    ci_lower: number;
    ci_upper: number;
    probability_improvement: number;
    probability_deterioration: number;
    uncertainty_score: number;
    extrapolation_warnings: string[];
  };
  monte_carlo: {
    iterations: number;
    expected_value: number;
    median: number;
    p05: number;
    p25: number;
    p75: number;
    p95: number;
    tail_risk: number;
    distribution: number[];
    methodology: string;
  };
  constraint_evaluations: Array<{
    satisfied: boolean;
    message: string;
    actual_value: number | null;
  }>;
  risk: {
    overall_score: number;
    implementation_risk: number;
    statistical_uncertainty: number;
    summary: string;
    contributors: Array<{ name: string; score: number; explanation: string }>;
  };
  roi: {
    expected_cost: number;
    expected_revenue: number;
    expected_savings: number;
    expected_roi: number;
    payback_period: number | null;
    cost_benefit_ratio: number;
    assumptions: string[];
  };
  comparison: Array<{
    scenario_id: string;
    scenario_name: string;
    expected_outcome: number;
    expected_roi: number | null;
    risk_score: number;
    rank: number;
  }>;
  interpretation: {
    scenario_summary: string;
    business_interpretation: string;
    limitations: string[];
    recommended_actions: string[];
    alternative_scenarios: string[];
  };
  assumptions: string[];
}

export interface RunSimulationRequest {
  dataset_id: string;
  version_id?: string;
  causal_analysis_id: string;
  statistical_analysis_id?: string;
  scenario_id?: string;
  name: string;
  objective: string;
  interventions?: Intervention[];
  constraints?: Constraint[];
  monte_carlo_iterations?: number;
  confidence_level?: number;
  roi_assumptions?: Record<string, number>;
}

export interface CreateScenarioRequest {
  dataset_id: string;
  version_id?: string;
  name: string;
  description?: string;
  objective?: string;
  interventions: Intervention[];
  constraints?: Constraint[];
}
