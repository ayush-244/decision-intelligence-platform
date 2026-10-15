import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import {
  exportExecutiveReport,
  fetchDecisionHistoryForReports,
  fetchExecutiveDashboard,
  fetchExecutiveReport,
  fetchExecutiveReportHistory,
  generateExecutiveReport,
} from '@/features/executive/api/endpoints';
import type { GenerateReportRequest } from '@/features/executive/types';
import { getAccessToken } from '@/features/auth/session';

export const executiveKeys = {
  history: (datasetId: string) => ['executive', 'history', datasetId] as const,
  report: (reportId: string) => ['executive', 'report', reportId] as const,
  dashboard: (datasetId: string) => ['executive', 'dashboard', datasetId] as const,
  decisions: (datasetId: string) => ['executive', 'decisions', datasetId] as const,
};

export function useExecutiveReportHistoryQuery(datasetId: string | undefined) {
  return useQuery({
    queryKey: executiveKeys.history(datasetId ?? ''),
    queryFn: () => fetchExecutiveReportHistory(datasetId!),
    enabled: Boolean(datasetId && getAccessToken()),
  });
}

export function useExecutiveReportQuery(reportId: string | undefined) {
  return useQuery({
    queryKey: executiveKeys.report(reportId ?? ''),
    queryFn: () => fetchExecutiveReport(reportId!),
    enabled: Boolean(reportId && getAccessToken()),
  });
}

export function useExecutiveDashboardQuery(datasetId: string | undefined) {
  return useQuery({
    queryKey: executiveKeys.dashboard(datasetId ?? ''),
    queryFn: () => fetchExecutiveDashboard(datasetId!),
    enabled: Boolean(datasetId && getAccessToken()),
  });
}

export function useDecisionsForReportQuery(datasetId: string | undefined) {
  return useQuery({
    queryKey: executiveKeys.decisions(datasetId ?? ''),
    queryFn: () => fetchDecisionHistoryForReports(datasetId!),
    enabled: Boolean(datasetId && getAccessToken()),
  });
}

export function useGenerateReportMutation(datasetId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: GenerateReportRequest) => generateExecutiveReport(body),
    onSuccess: (result) => {
      if (datasetId) {
        void queryClient.invalidateQueries({ queryKey: executiveKeys.history(datasetId) });
        void queryClient.invalidateQueries({ queryKey: executiveKeys.dashboard(datasetId) });
      }
      toast.success('Executive report generated', {
        description: result.result?.executive_summary?.slice(0, 120),
      });
    },
    onError: (error: Error) => {
      toast.error('Report generation failed', { description: error.message });
    },
  });
}

export function useExportReportMutation() {
  return useMutation({
    mutationFn: ({
      reportId,
      format,
    }: {
      reportId: string;
      format: 'markdown' | 'csv' | 'json' | 'pdf';
    }) => exportExecutiveReport(reportId, format),
    onSuccess: (data) => {
      const blob = new Blob([data.content], { type: data.media_type });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = data.filename;
      anchor.click();
      URL.revokeObjectURL(url);
      toast.success('Report exported', { description: data.filename });
    },
    onError: (error: Error) => {
      toast.error('Export failed', { description: error.message });
    },
  });
}
