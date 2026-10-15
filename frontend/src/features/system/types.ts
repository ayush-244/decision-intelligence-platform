export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy';

export interface ComponentHealth {
  name: string;
  status: HealthStatus;
  detail: string | null;
  latency_ms: number | null;
}

export interface HealthResponse {
  status: HealthStatus;
  components: ComponentHealth[];
}

export interface VersionResponse {
  name: string;
  version: string;
  environment: string;
}
