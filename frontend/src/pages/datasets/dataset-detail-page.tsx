import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useState } from 'react';
import { toast } from 'sonner';
import {
  Brain,
  FileText,
  FlaskConical,
  LayoutDashboard,
  Lightbulb,
  Network,
  Sigma,
  Trash2,
  Upload,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  formatBytes,
  useDatasetPreviewQuery,
  useDatasetQuery,
  useDatasetVersionsQuery,
  useDeleteDatasetMutation,
  useUploadDatasetVersionMutation,
} from '@/features/datasets';

function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) {
    return '';
  }
  if (typeof value === 'object') {
    return JSON.stringify(value);
  }
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }
  return JSON.stringify(value);
}

export function DatasetDetailPage() {
  const navigate = useNavigate();
  const { datasetId } = useParams<{ datasetId: string }>();
  const [searchParams] = useSearchParams();
  const projectId = searchParams.get('project_id') ?? '';
  const [versionId, setVersionId] = useState<string | undefined>();

  const dataset = useDatasetQuery(datasetId);
  const versions = useDatasetVersionsQuery(datasetId);
  const preview = useDatasetPreviewQuery(datasetId, versionId);
  const uploadVersion = useUploadDatasetVersionMutation();
  const deleteDataset = useDeleteDatasetMutation();

  async function handleNewVersion(file: File) {
    if (!datasetId) return;
    try {
      const result = await uploadVersion.mutateAsync({ datasetId, file });
      toast.success(`Version ${result.version.version_number} uploaded`);
      setVersionId(result.version.id);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Upload failed.');
    }
  }

  async function handleDelete() {
    if (!datasetId || !projectId) return;
    try {
      await deleteDataset.mutateAsync({ datasetId, projectId });
      toast.success('Dataset deleted');
      void navigate(`/app/datasets?project_id=${projectId}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Delete failed.');
    }
  }

  if (dataset.isLoading) {
    return <p className="text-muted-foreground text-sm">Loading dataset…</p>;
  }

  const row = dataset.data;
  if (!row) {
    return <p className="text-muted-foreground text-sm">Dataset not found.</p>;
  }

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-muted-foreground text-sm">
            <Link className="hover:underline" to={`/app/datasets?project_id=${projectId}`}>
              Datasets
            </Link>{' '}
            / {row.name}
          </p>
          <h2 className="text-display text-2xl sm:text-[1.75rem]">{row.name}</h2>
          {row.description ? (
            <p className="text-muted-foreground mt-1 text-sm">{row.description}</p>
          ) : null}
        </div>
        <div className="flex gap-2">
          <Button asChild variant="default">
            <Link to={`/app/workspace/${datasetId}?project_id=${projectId}`}>
              <LayoutDashboard className="size-4" />
              Workspace
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link to={`/app/datasets/${datasetId}/intelligence?project_id=${projectId}`}>
              <Brain className="size-4" />
              Intelligence
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link to={`/app/datasets/${datasetId}/statistics?project_id=${projectId}`}>
              <Sigma className="size-4" />
              Statistics
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link to={`/app/datasets/${datasetId}/causal?project_id=${projectId}`}>
              <Network className="size-4" />
              Causal
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link to={`/app/datasets/${datasetId}/simulation?project_id=${projectId}`}>
              <FlaskConical className="size-4" />
              Simulation
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link to={`/app/datasets/${datasetId}/executive?project_id=${projectId}`}>
              <FileText className="size-4" />
              Executive
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link to={`/app/datasets/${datasetId}/decision?project_id=${projectId}`}>
              <Lightbulb className="size-4" />
              Decisions
            </Link>
          </Button>
          <label>
            <Button asChild variant="outline" disabled={uploadVersion.isPending}>
              <span>
                <Upload className="size-4" />
                New version
              </span>
            </Button>
            <input
              type="file"
              accept=".csv,.xlsx,.parquet"
              className="hidden"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) void handleNewVersion(file);
              }}
            />
          </label>
          <Button
            variant="destructive"
            size="icon"
            onClick={() => {
              void handleDelete();
            }}
          >
            <Trash2 className="size-4" />
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Latest version</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">
            {row.latest_version ? `v${row.latest_version.version_number}` : '—'}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Rows</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">
            {row.latest_version?.row_count.toLocaleString() ?? '—'}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Columns</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">
            {row.latest_version?.column_count ?? '—'}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Version history</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2">
            {(versions.data ?? []).map((version) => (
              <li key={version.id}>
                <button
                  type="button"
                  className="hover:bg-muted/50 flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm"
                  onClick={() => setVersionId(version.id)}
                >
                  <span>v{version.version_number}</span>
                  <span className="text-muted-foreground">
                    {formatBytes(version.file_size_bytes)} · {version.validation_status}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Preview</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          {preview.isLoading ? (
            <p className="text-muted-foreground text-sm">Loading preview…</p>
          ) : preview.data ? (
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b text-left">
                  {preview.data.columns.map((col) => (
                    <th key={col.name} className="px-2 py-2 font-medium">
                      {col.name}
                      <span className="text-muted-foreground block font-normal">
                        {col.semantic_type}
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.data.rows.map((rowData, index) => (
                  <tr key={index} className="border-b">
                    {preview.data.columns.map((col) => (
                      <td key={col.name} className="px-2 py-2">
                        {formatCellValue(rowData[col.name])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
