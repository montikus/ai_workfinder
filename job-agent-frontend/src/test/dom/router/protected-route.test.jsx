import React from 'react';
import { Route, Routes } from 'react-router-dom';
import { screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ProtectedRoute } from '../../../router/ProtectedRoute.jsx';
import { useAuth } from '../../../context/AuthContext.jsx';
import { renderWithProviders } from '../../helpers/renderWithProviders.jsx';

vi.mock('../../../context/AuthContext.jsx', () => ({
  useAuth: vi.fn(),
}));

describe('ProtectedRoute', () => {
  it('shows loading state while auth is resolving', () => {
    useAuth.mockReturnValue({ zalogowany: false, ladowanie: true });

    renderWithProviders(
      <Routes>
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<div>Secret</div>} />
        </Route>
      </Routes>,
      { route: '/dashboard' }
    );

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('redirects unauthenticated users to login', () => {
    useAuth.mockReturnValue({ zalogowany: false, ladowanie: false });

    renderWithProviders(
      <Routes>
        <Route path="/login" element={<div>Login page</div>} />
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<div>Secret</div>} />
        </Route>
      </Routes>,
      { route: '/dashboard' }
    );

    expect(screen.getByText('Login page')).toBeInTheDocument();
  });

  it('renders the outlet for authenticated users', () => {
    useAuth.mockReturnValue({ zalogowany: true, ladowanie: false });

    renderWithProviders(
      <Routes>
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<div>Secret</div>} />
        </Route>
      </Routes>,
      { route: '/dashboard' }
    );

    expect(screen.getByText('Secret')).toBeInTheDocument();
  });
});
