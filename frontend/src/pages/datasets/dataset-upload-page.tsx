import { useCallback, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';
import { Upload } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input, Label } from '@/components/ui/input';
import { useUploadDatasetMutation } from '@/features/datasets';
import { cn } from '@/lib/utils';

const ACCEPT = '.csv,.xlsx,.parquet';

export function DatasetUploadPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const projectId = searchParams.get('project_id') ?? '';
  const upload = useUploadDatasetMutation();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFile = useCallback((file: File | null) => {
    setSelectedFile(file);
    if (file && !name) {
      setName(file.name.replace(/\.[^.]+$/, ''));
    }
  }, [name]);

  async function handleUpload() {
    if (!projectId || !selectedFile) {
      toast.error('Select a project and file before uploading.');
      return;
    }
    try {
      const result = await upload.mutateAsync({
        projectId,
        file: selectedFile,
        ...(name ? { name } : {}),
        ...(description ? { description } : {}),
      });
      toast.success(`Dataset uploaded — v${result.version.version_number}`, {
        description: `${result.version.row_count.toLocaleString()} rows · ${result.version.column_count} columns`,
      });
      void navigate(`/app/datasets/${result.dataset.id}?project_id=${projectId}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Upload failed.');
    }
  }

  if (!projectId) {
    return (
      <div className="mx-auto max-w-lg py-12 text-center">
        <p className="text-muted-foreground">Missing project context.</p>
        <Button asChild className="mt-4" variant="outline">
          <Link to="/app/workspaces">Back to workspaces</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-6">
      <div>
        <h2 className="text-display text-2xl sm:text-[1.75rem]">Upload dataset</h2>
        <p className="text-muted-foreground mt-1 text-sm">CSV, Excel (.xlsx), or Parquet.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">File</CardTitle>
          <CardDescription>Drag and drop or browse. Max 100 MiB.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <label
            className={cn(
              'border-border flex cursor-pointer flex-col items-center gap-3 rounded-lg border border-dashed p-10 transition-colors',
              dragOver && 'border-primary bg-primary/5',
            )}
            onDragOver={(event) => {
              event.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(event) => {
              event.preventDefault();
              setDragOver(false);
              handleFile(event.dataTransfer.files[0] ?? null);
            }}
          >
            <Upload className="text-muted-foreground size-8" />
            <span className="text-sm">
              {selectedFile ? selectedFile.name : 'Drop file here or click to browse'}
            </span>
            <input
              type="file"
              accept={ACCEPT}
              className="sr-only"
              onChange={(event) => handleFile(event.target.files?.[0] ?? null)}
            />
          </label>

          <div className="space-y-2">
            <Label htmlFor="datasetName">Dataset name</Label>
            <Input
              id="datasetName"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Sales Q3 2026"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="datasetDescription">Description</Label>
            <Input
              id="datasetDescription"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          </div>

          <Button
            disabled={!selectedFile || upload.isPending}
            onClick={() => { void handleUpload(); }}
          >
            {upload.isPending ? 'Uploading…' : 'Upload and validate'}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
