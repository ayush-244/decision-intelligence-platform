import { apiFetchData } from '@/services/api/client';

import type {
  CreateScenarioRequest,
  RunSimulationRequest,
  SimulationRun,
  SimulationScenario,
} from '@/features/simulation/types';

export async function runSimulation(body: RunSimulationRequest): Promise<SimulationRun> {
  return apiFetchData<SimulationRun>('/api/v1/simulations', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function fetchSimulation(simulationId: string): Promise<SimulationRun> {
  return apiFetchData<SimulationRun>(`/api/v1/simulations/${simulationId}`);
}

export async function fetchSimulationHistory(datasetId: string): Promise<SimulationRun[]> {
  return apiFetchData<SimulationRun[]>(
    `/api/v1/simulations/history?dataset_id=${datasetId}`,
  );
}

export async function createScenario(body: CreateScenarioRequest): Promise<SimulationScenario> {
  return apiFetchData<SimulationScenario>('/api/v1/scenarios', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function fetchScenarios(datasetId: string): Promise<SimulationScenario[]> {
  return apiFetchData<SimulationScenario[]>(`/api/v1/scenarios?dataset_id=${datasetId}`);
}

export async function fetchCausalHistoryForSimulation(
  datasetId: string,
): Promise<Array<{ id: string; treatment: string; outcome: string; status: string }>> {
  return apiFetchData(`/api/v1/causal/history?dataset_id=${datasetId}`);
}
