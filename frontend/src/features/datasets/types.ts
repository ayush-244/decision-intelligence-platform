/** Dataset wire types mirroring backend schemas. */

export type DataSourceFormat = 'csv' | 'xlsx' | 'parquet';
export type ValidationStatus = 'pending' | 'passed' | 'failed' | 'warning';
export type UploadJobStatus = 'pending' | 'validating' | 'processing' | 'completed' | 'failed';
export type ColumnSemanticType =
  | 'integer'
  | 'float'
  | 'boolean'
  | 'categorical'
  | 'datetime'
  | 'text'
  | 'identifier'
  | 'ordinal';

export interface ColumnMetadata {
  name: string;
  position: number;
  semantic_type: ColumnSemanticType;
  storage_type: string;
  null_percentage: number;
  distinct_count: number | null;
  example_values: string[];
  type_confidence: number;
}

export interface DatasetVersion {
  id: string;
  dataset_id: string;
  version_number: number;
  uploaded_by: string;
  source_format: DataSourceFormat;
  file_hash: string;
  schema_hash: string;
  row_count: number;
  column_count: number;
  file_size_bytes: number;
  validation_status: ValidationStatus;
  created_at: string;
}

export interface Dataset {
  id: string;
  project_id: string;
  organization_id: string;
  name: string;
  slug: string;
  description: string | null;
  created_by: string;
  current_version_id: string | null;
  created_at: string;
  updated_at: string;
  latest_version: DatasetVersion | null;
}

export interface ValidationReport {
  status: ValidationStatus;
  checks: Record<string, boolean>;
  errors: string[];
  warnings: string[];
}

export interface UploadResult {
  dataset: Dataset;
  version: DatasetVersion;
  job_id: string;
  job_status: UploadJobStatus;
  validation: ValidationReport;
  preview_rows: Record<string, unknown>[];
}

export interface DatasetPreview {
  dataset_id: string;
  version_id: string;
  version_number: number;
  row_count: number;
  column_count: number;
  columns: ColumnMetadata[];
  rows: Record<string, unknown>[];
  validation: ValidationReport | null;
}
