import { Building2, Plus } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input, Label } from '@/components/ui/input';
import {
  persistOrganizationSelection,
  useCreateOrganizationMutation,
  useOrganizationsQuery,
} from '@/features/auth/hooks';
import { ApiError } from '@/services/api/client';

export function OrganizationSelectorPage() {
  const navigate = useNavigate();
  const organizations = useOrganizationsQuery();
  const createOrganization = useCreateOrganizationMutation();
  const [name, setName] = useState('');
  const [error, setError] = useState<string | null>(null);

  function selectOrganization(organizationId: string) {
    persistOrganizationSelection(organizationId);
    void navigate('/app/workspaces');
  }

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      const organization = await createOrganization.mutateAsync({ name });
      selectOrganization(organization.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not create organization.');
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-6">
      <div>
        <h2 className="text-display text-2xl sm:text-[1.75rem]">Choose an organization</h2>
        <p className="text-muted-foreground mt-1 text-sm">
          Organizations are the top-level tenant boundary for workspaces and projects.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {organizations.data?.map((organization) => (
          <Card
            key={organization.id}
            className="hover:border-foreground/20 cursor-pointer transition-colors"
          >
            <button
              type="button"
              className="w-full text-left"
              onClick={() => selectOrganization(organization.id)}
            >
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="bg-muted flex size-10 items-center justify-center rounded-md">
                    <Building2 className="size-4" />
                  </div>
                  <div>
                    <CardTitle className="text-base">{organization.name}</CardTitle>
                    <CardDescription>{organization.role}</CardDescription>
                  </div>
                </div>
              </CardHeader>
            </button>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Plus className="size-4" />
            Create organization
          </CardTitle>
          <CardDescription>Set up a new tenant for your team.</CardDescription>
        </CardHeader>
        <CardContent>
          <form
            className="flex flex-col gap-4 sm:flex-row sm:items-end"
            onSubmit={(event) => {
              void handleCreate(event);
            }}
          >
            <div className="flex-1 space-y-2">
              <Label htmlFor="orgName">Organization name</Label>
              <Input
                id="orgName"
                required
                value={name}
                onChange={(event) => setName(event.target.value)}
              />
            </div>
            <Button type="submit" disabled={createOrganization.isPending}>
              Create
            </Button>
          </form>
          {error ? <p className="text-destructive mt-3 text-sm">{error}</p> : null}
        </CardContent>
      </Card>
    </div>
  );
}
