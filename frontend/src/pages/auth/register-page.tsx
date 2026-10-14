import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { Button } from '@/components/ui/button';
import { Input, Label } from '@/components/ui/input';
import { useRegisterMutation } from '@/features/auth/hooks';
import { ApiError } from '@/services/api/client';

import { AuthShell } from './auth-shell';

export function RegisterPage() {
  const navigate = useNavigate();
  const register = useRegisterMutation();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await register.mutateAsync({ email, password, full_name: fullName });
      void navigate('/login');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Registration failed.');
    }
  }

  return (
    <AuthShell
      title="Create your account"
      subtitle="Start building causal decision intelligence in minutes."
    >
      <form
        className="flex flex-col gap-5"
        onSubmit={(event) => {
          void handleSubmit(event);
        }}
      >
        <div className="space-y-2">
          <Label htmlFor="fullName">Full name</Label>
          <Input
            id="fullName"
            required
            placeholder="Ada Lovelace"
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
          />
        </div>
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
            autoComplete="new-password"
            required
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          <p className="text-muted-foreground text-xs">
            At least 8 characters with a letter and a number.
          </p>
        </div>
        {error ? (
          <p role="alert" className="text-destructive text-sm">
            {error}
          </p>
        ) : null}
        <Button type="submit" size="lg" disabled={register.isPending}>
          {register.isPending ? 'Creating account…' : 'Create account'}
        </Button>
      </form>
      <p className="text-muted-foreground mt-6 text-sm">
        Already have an account?{' '}
        <Link className="text-primary font-medium underline-offset-4 hover:underline" to="/login">
          Sign in
        </Link>
      </p>
    </AuthShell>
  );
}
