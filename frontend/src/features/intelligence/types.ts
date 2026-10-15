/** Data intelligence API types (mirror backend report sections). */

export interface IntelligenceAnalyzeResult {
  status: string;
  quality_score: number | null;
  health_score: number | null;
  rows_sampled: number;
  total_rows: number;
  version_id: string;
  computed_at: string | null;
}

export interface ScoreComponent {
  name: string;
  score: number;
  weight: number;
  explanation: string;
}

export interface DataQualitySection {
  overall_score: number;
  completeness: number;
  consistency: number;
  uniqueness: number;
  validity: number;
  integrity: number;
  duplicate_percentage: number;
  constant_columns: string[];
  near_constant_columns: string[];
  high_cardinality_columns: string[];
  issues: string[];
  components: ScoreComponent[];
}

export interface ColumnIntelligence {
  name: string;
  semantic_type: string;
  suggested_role: string;
  identifier_probability: number;
  null_percentage: number;
  distinct_count: number;
  usability_score: number;
  potential_issues: string[];
  business_interpretation: string;
  mean?: number | null;
  std_dev?: number | null;
}

export interface IntelligenceOverview {
  dataset_id: string;
  version_id: string;
  version_number: number;
  row_count: number;
  column_count: number;
  rows_sampled: number;
  quality_score: number;
  health_score: number;
  trust_level: string;
  headline_findings: string[];
}

export interface DataHealthSection {
  overall_score: number;
  explanation?: string;
  category_scores?: Record<string, number>;
  improvement_suggestions?: string[];
}

export interface IntelligenceReport {
  status: string;
  quality_score: number | null;
  health_score: number | null;
  rows_sampled: number;
  total_rows: number;
  computed_at: string | null;
  overview: IntelligenceOverview;
  data_quality: DataQualitySection;
  columns: ColumnIntelligence[];
  missing_data: Record<string, unknown>;
  outliers: Record<string, unknown>;
  correlations: Record<string, unknown>;
  distributions: Record<string, unknown>[];
  data_health: DataHealthSection;
  analytical_readiness: Record<string, unknown>;
  recommendations: string[];
}

export interface IntelligenceSummary {
  overview: IntelligenceOverview;
  data_health: Record<string, unknown>;
  analytical_readiness: Record<string, unknown>;
  recommendations: string[];
  quality_score: number | null;
  health_score: number | null;
}
