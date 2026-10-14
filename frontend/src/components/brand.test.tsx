import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Brand } from './brand';

describe('Brand', () => {
  it('renders the Delphi wordmark', () => {
    render(<Brand />);
    expect(screen.getByText('Delphi')).toBeInTheDocument();
  });
});
