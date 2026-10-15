import { apiFetchData } from '@/services/api/client';

import type {
  ExecutiveDashboard,
  ExecutiveReport,
  ExecutiveReportHistoryItem,
  ExportReportResponse,
  GenerateReportRequest,
} from '@/features/executive/types';

export async function generateExecutiveReport(
  body: GenerateReportRequest,
): Promise<ExecutiveReport> {
  return apiFetchData<ExecutiveReport>('/api/v1/reports/generate', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function fetchExecutiveReport(reportId: string): Promise<ExecutiveReport> {
  return apiFetchData<ExecutiveReport>(`/api/v1/reports/${reportId}`);
}

export async function fetchExecutiveReportHistory(
  datasetId: string,
): Promise<ExecutiveReportHistoryItem[]> {
  return apiFetchData<ExecutiveReportHistoryItem[]>(
    `/api/v1/reports?dataset_id=${datasetId}`,
  );
}

export async function exportExecutiveReport(
  reportId: string,
  format: 'markdown' | 'csv' | 'json' | 'pdf',
): Promise<ExportReportResponse> {
  return apiFetchData<ExportReportResponse>(
    `/api/v1/reports/export?report_id=${reportId}`,
    {
      method: 'POST',
      body: JSON.stringify({ format }),
    },
  );
}

export async function fetchExecutiveDashboard(datasetId: string): Promise<ExecutiveDashboard> {
  return apiFetchData<ExecutiveDashboard>(
    `/api/v1/executive/dashboard?dataset_id=${datasetId}`,
  );
}

export async function fetchDecisionHistoryForReports(
  datasetId: string,
): Promise<Array<{ id: string; name: string; status: string }>> {
  return apiFetchData(`/api/v1/decisions?dataset_id=${datasetId}`);
}
