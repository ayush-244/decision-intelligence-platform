import { FlaskConical, Plus } from 'lucide-react';
import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input, Label } from '@/components/ui/input';
import { useCreateProjectMutation, useProjectsQuery } from '@/features/auth/hooks';
import { ApiError } from '@/services/api/client';

export function ProjectDashboardPage() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const projects = useProjectsQuery(workspaceId);
  const createProject = useCreateProjectMutation();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState<string | null>(null);

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    if (!workspaceId) {
      return;
    }
    setError(null);
    try {
      await createProject.mutateAsync({
        workspace_id: workspaceId,
        name,
        ...(description ? { description } : {}),
      });
      setName('');
      setDescription('');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not create project.');
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-muted-foreground text-sm">
            <Link className="hover:underline" to="/app/workspaces">
              Workspaces
            </Link>{' '}
            / Projects
          </p>
          <h2 className="text-display text-2xl sm:text-[1.75rem]">Projects</h2>
          <p className="text-muted-foreground mt-1 text-sm">
            Analytical work units where datasets and simulations will attach in later phases.
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {projects.data?.map((project) => (
          <Card key={project.id}>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="bg-muted flex size-10 items-center justify-center rounded-md">
                  <FlaskConical className="size-4" />
                </div>
                <div>
                  <CardTitle className="text-base">{project.name}</CardTitle>
                  <CardDescription>{project.description ?? 'No description'}</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Button asChild variant="outline" size="sm">
                <Link to={`/app/datasets?project_id=${project.id}`}>Manage datasets</Link>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Plus className="size-4" />
            New project
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="grid gap-4 md:grid-cols-2"
            onSubmit={(event) => {
              void handleCreate(event);
            }}
          >
            <div className="space-y-2">
              <Label htmlFor="projectName">Name</Label>
              <Input
                id="projectName"
                required
                value={name}
                onChange={(event) => setName(event.target.value)}
              />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="projectDescription">Description</Label>
              <Input
                id="projectDescription"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
              />
            </div>
            <div className="md:col-span-2">
              <Button type="submit" disabled={createProject.isPending || !workspaceId}>
                Create project
              </Button>
            </div>
          </form>
          {error ? <p className="text-destructive mt-3 text-sm">{error}</p> : null}
        </CardContent>
      </Card>
    </div>
  );
}
