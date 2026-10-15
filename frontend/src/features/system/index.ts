/**
 * System feature — health checks and service metadata.
 *
 * Reference implementation of the feature-first module pattern documented in
 * `src/features/README.md`. Future features should mirror this layout.
 */
export type {
  ComponentHealth,
  HealthResponse,
  HealthStatus,
  VersionResponse,
} from '@/features/system/types';
export { getHealth, getVersion } from '@/features/system/api/endpoints';
export { systemKeys, useHealthQuery, useVersionQuery } from '@/features/system/hooks';
