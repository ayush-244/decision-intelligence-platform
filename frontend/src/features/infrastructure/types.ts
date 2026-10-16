export interface JobSnapshot {
  id: string;
  job_type: string;
  status: string;
  name: string;
  progress: number;
  error_message: string | null;
  retry_count: number;
  logs: string[];
  queued_at: string;
  started_at: string | null;
  completed_at: string | null;
  estimated_duration_ms: number | null;
  duration_ms: number | null;
}

export interface InfrastructureMetrics {
  queue_depth: number;
  jobs_queued: number;
  jobs_running: number;
  jobs_completed_24h: number;
  jobs_failed_24h: number;
  cache_hits: number;
  cache_misses: number;
  cache_keys: number;
  avg_job_duration_ms: number | null;
  slow_queries_detected: number;
}

export interface SubmitJobRequest {
  job_type: string;
  name: string;
  dataset_id?: string;
  version_id?: string;
  resource_type?: string;
  resource_id?: string;
  configuration?: Record<string, unknown>;
}
