import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { QueryProvider } from '@/app/providers/query-provider';
import { LoginPage } from '@/pages/auth/login-page';

describe('LoginPage', () => {
  it('renders the sign-in form', () => {
    render(
      <QueryProvider>
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      </QueryProvider>,
    );

    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument();
  });
});
