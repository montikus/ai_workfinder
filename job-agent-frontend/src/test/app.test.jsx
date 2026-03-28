import React from 'react';
import { screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import App from '../App.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import { renderWithProviders } from './renderWithProviders.jsx';

vi.mock('../context/AuthContext.jsx', () => ({
  useAuth: vi.fn(),
}));

describe('App', () => {
  it('renders the login route', () => {
    useAuth.mockReturnValue({ zalogowany: false, ladowanie: false, zaloguj: vi.fn() });

    renderWithProviders(<App />, { route: '/login' });

    expect(screen.getByRole('heading', { name: 'Login' })).toBeInTheDocument();
  });

  it('redirects unknown routes to login when the user is not authenticated', () => {
    useAuth.mockReturnValue({ zalogowany: false, ladowanie: false, zaloguj: vi.fn() });

    renderWithProviders(<App />, { route: '/unknown' });

    expect(screen.getByRole('heading', { name: 'Login' })).toBeInTheDocument();
  });
});
