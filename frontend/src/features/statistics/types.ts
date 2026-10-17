/** Statistical analysis API types. */

export type AnalysisGoal =
  | 'describe'
  | 'compare_groups'
  | 'compare_paired'
  | 'association'
  | 'predict_continuous'
  | 'predict_binary'
  | 'test_change';

export interface VariableSpec {
  name: string;
  role: 'outcome' | 'predictor' | 'grouping' | 'covariate' | 'identifier';
}

export interface TestRecommendation {
  recommended_test: string;
  confidence: number;
  reasoning: string;
  expected_assumptions: string[];
  limitations: string[];
  alternatives: string[];
}

export interface AssumptionCheck {
  name: string;
  status: string;
  statistic: number | null;
  p_value: number | null;
  explanation: string;
  recommendation: string | null;
}

export interface EffectSize {
  name: string;
  value: number;
  interpretation: string;
  magnitude: string;
}

export interface ConfidenceInterval {
  parameter: string;
  lower: number;
  upper: number;
  level: number;
  interpretation: string;
}

export interface AnalysisInterpretation {
  test_performed: string;
  selection_reason: string;
  practical_significance: string;
  business_interpretation: string;
  limitations: string[];
  recommended_next_steps: string[];
}

export interface AnalysisResult {
  assumption_report: {
    checks: AssumptionCheck[];
    all_passed: boolean;
    alternatives: string[];
  };
  test_result: {
    test_type: string;
    statistic: number | null;
    p_value: number | null;
    is_significant: boolean;
    alpha: number;
    details: Record<string, unknown>;
  } | null;
  effect_sizes: EffectSize[];
  confidence_intervals: ConfidenceInterval[];
  regression: Record<string, unknown> | null;
  interpretation: AnalysisInterpretation;
  descriptive: Record<string, unknown>;
}

export interface AnalysisRun {
  id: string;
  dataset_id: string;
  version_id: string;
  status: string;
  goal: string;
  test_type: string | null;
  research_question: string;
  error_message: string | null;
  executed_at: string | null;
  created_at: string;
  result: AnalysisResult;
}

export interface AnalysisHistoryItem {
  id: string;
  dataset_id: string;
  version_id: string;
  status: string;
  goal: string;
  test_type: string | null;
  executed_at: string | null;
  created_at: string;
}

export interface AnalyzeRequest {
  dataset_id: string;
  version_id?: string;
  goal: AnalysisGoal;
  research_question: string;
  variables: VariableSpec[];
  test_type?: string;
  confidence_level?: number;
  reference_value?: number;
}

export const ANALYSIS_GOALS: { value: AnalysisGoal; label: string; description: string }[] = [
  {
    value: 'describe',
    label: 'Describe data',
    description: 'Summarize central tendency and spread',
  },
  {
    value: 'compare_groups',
    label: 'Compare groups',
    description: 'Test if two or more groups differ',
  },
  {
    value: 'compare_paired',
    label: 'Compare paired measurements',
    description: 'Before/after or matched pairs',
  },
  {
    value: 'association',
    label: 'Find associations',
    description: 'Relationship between variables',
  },
  { value: 'predict_continuous', label: 'Predict a number', description: 'Linear regression' },
  {
    value: 'predict_binary',
    label: 'Predict a category',
    description: 'Logistic regression (foundation)',
  },
  {
    value: 'test_change',
    label: 'Test if a metric changed',
    description: 'One-sample or group comparison',
  },
];

export const VARIABLE_ROLES: { value: VariableSpec['role']; label: string }[] = [
  { value: 'outcome', label: 'Outcome (Y)' },
  { value: 'predictor', label: 'Predictor (X)' },
  { value: 'grouping', label: 'Grouping' },
  { value: 'covariate', label: 'Covariate' },
];
