import { FolderKanban, Plus } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input, Label } from '@/components/ui/input';
import { getActiveOrganizationId } from '@/features/auth/session';
import { useCreateWorkspaceMutation, useWorkspacesQuery } from '@/features/auth/hooks';
import { ApiError } from '@/services/api/client';

export function WorkspaceDashboardPage() {
  const organizationId = getActiveOrganizationId();
  const workspaces = useWorkspacesQuery();
  const createWorkspace = useCreateWorkspaceMutation();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState<string | null>(null);

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    if (!organizationId) {
      return;
    }
    setError(null);
    try {
      await createWorkspace.mutateAsync({
        organization_id: organizationId,
        name,
        ...(description ? { description } : {}),
      });
      setName('');
      setDescription('');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not create workspace.');
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
      <div>
        <h2 className="text-display text-2xl sm:text-[1.75rem]">Workspaces</h2>
        <p className="text-muted-foreground mt-1 text-sm">
          Partition projects and future datasets within your organization.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {workspaces.data?.map((workspace) => (
          <Card key={workspace.id}>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="bg-muted flex size-10 items-center justify-center rounded-md">
                  <FolderKanban className="size-4" />
                </div>
                <div>
                  <CardTitle className="text-base">{workspace.name}</CardTitle>
                  <CardDescription>{workspace.description ?? 'No description'}</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Button asChild variant="outline" size="sm">
                <Link to={`/app/workspaces/${workspace.id}/projects`}>Open projects</Link>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Plus className="size-4" />
            New workspace
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form className="grid gap-4 md:grid-cols-2" onSubmit={(event) => { void handleCreate(event); }}>
            <div className="space-y-2">
              <Label htmlFor="workspaceName">Name</Label>
              <Input
                id="workspaceName"
                required
                value={name}
                onChange={(event) => setName(event.target.value)}
              />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="workspaceDescription">Description</Label>
              <Input
                id="workspaceDescription"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
              />
            </div>
            <div className="md:col-span-2">
              <Button type="submit" disabled={createWorkspace.isPending || !organizationId}>
                Create workspace
              </Button>
            </div>
          </form>
          {error ? <p className="text-destructive mt-3 text-sm">{error}</p> : null}
        </CardContent>
      </Card>
    </div>
  );
}
