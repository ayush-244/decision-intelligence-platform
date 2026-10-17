import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { Button } from '@/components/ui/button';
import { Input, Label } from '@/components/ui/input';
import { useLoginMutation } from '@/features/auth/hooks';
import { ApiError } from '@/services/api/client';

import { AuthShell } from './auth-shell';

export function LoginPage() {
  const navigate = useNavigate();
  const login = useLoginMutation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await login.mutateAsync({ email, password });
      void navigate('/app/organizations');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Login failed.');
    }
  }

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Sign in to your organizations, workspaces, and projects."
    >
      <form
        className="flex flex-col gap-5"
        onSubmit={(event) => {
          void handleSubmit(event);
        }}
      >
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            placeholder="you@company.com"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </div>
        {error ? (
          <p role="alert" className="text-destructive text-sm">
            {error}
          </p>
        ) : null}
        <Button type="submit" size="lg" disabled={login.isPending}>
          {login.isPending ? 'Signing in…' : 'Sign in'}
        </Button>
      </form>
      <p className="text-muted-foreground mt-6 text-sm">
        No account?{' '}
        <Link
          className="text-primary font-medium underline-offset-4 hover:underline"
          to="/register"
        >
          Create one
        </Link>
      </p>
    </AuthShell>
  );
}
