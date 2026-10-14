import { Link, useSearchParams } from 'react-router-dom';
import { Database, Plus, Upload } from 'lucide-react';
import { useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { formatBytes, useDatasetsQuery } from '@/features/datasets';

export function DatasetListPage() {
  const [searchParams] = useSearchParams();
  const projectId = searchParams.get('project_id') ?? undefined;
  const [filter, setFilter] = useState('');
  const datasets = useDatasetsQuery(projectId);

  const filtered = useMemo(() => {
    const rows = datasets.data ?? [];
    if (!filter.trim()) return rows;
    const q = filter.toLowerCase();
    return rows.filter((row) => row.name.toLowerCase().includes(q));
  }, [datasets.data, filter]);

  if (!projectId) {
    return (
      <div className="mx-auto max-w-2xl py-12 text-center">
        <p className="text-muted-foreground">Select a project to view datasets.</p>
        <Button asChild className="mt-4" variant="outline">
          <Link to="/app/workspaces">Go to workspaces</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-display text-2xl sm:text-[1.75rem]">Datasets</h2>
          <p className="text-muted-foreground mt-1 text-sm">
            Versioned, validated data assets for your project.
          </p>
        </div>
        <Button asChild>
          <Link to={`/app/datasets/upload?project_id=${projectId}`}>
            <Upload className="size-4" />
            Upload dataset
          </Link>
        </Button>
      </div>

      <Input
        placeholder="Search datasets…"
        value={filter}
        onChange={(event) => setFilter(event.target.value)}
        className="max-w-sm"
      />

      {datasets.isLoading ? (
        <p className="text-muted-foreground text-sm">Loading datasets…</p>
      ) : filtered.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-12">
            <Database className="text-muted-foreground size-10" />
            <p className="text-muted-foreground text-sm">No datasets yet. Upload your first file.</p>
            <Button asChild size="sm">
              <Link to={`/app/datasets/upload?project_id=${projectId}`}>
                <Plus className="size-4" />
                Upload
              </Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="overflow-x-auto rounded-lg border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 text-left">
              <tr>
                <th className="px-4 py-3 font-medium">Name</th>
                <th className="px-4 py-3 font-medium">Version</th>
                <th className="px-4 py-3 font-medium">Rows</th>
                <th className="px-4 py-3 font-medium">Columns</th>
                <th className="px-4 py-3 font-medium">Size</th>
                <th className="px-4 py-3 font-medium">Format</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((dataset) => (
                <tr key={dataset.id} className="border-t hover:bg-muted/30">
                  <td className="px-4 py-3">
                    <Link
                      className="font-medium hover:underline"
                      to={`/app/datasets/${dataset.id}?project_id=${projectId}`}
                    >
                      {dataset.name}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    {dataset.latest_version ? `v${dataset.latest_version.version_number}` : '—'}
                  </td>
                  <td className="px-4 py-3">
                    {dataset.latest_version?.row_count.toLocaleString() ?? '—'}
                  </td>
                  <td className="px-4 py-3">{dataset.latest_version?.column_count ?? '—'}</td>
                  <td className="px-4 py-3">
                    {dataset.latest_version
                      ? formatBytes(dataset.latest_version.file_size_bytes)
                      : '—'}
                  </td>
                  <td className="px-4 py-3 uppercase">
                    {dataset.latest_version?.source_format ?? '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
