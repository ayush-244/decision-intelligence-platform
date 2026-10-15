import { useQuery } from '@tanstack/react-query';

import { getHealth, getVersion } from '@/features/system/api/endpoints';

/** Query keys are centralised so cache invalidation stays consistent. */
export const systemKeys = {
  health: ['system', 'health'] as const,
  version: ['system', 'version'] as const,
};

export function useHealthQuery() {
  return useQuery({
    queryKey: systemKeys.health,
    queryFn: getHealth,
    refetchInterval: 15_000,
  });
}

export function useVersionQuery() {
  return useQuery({
    queryKey: systemKeys.version,
    queryFn: getVersion,
    staleTime: Infinity,
  });
}
