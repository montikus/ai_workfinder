import React from 'react';
import { Route, Routes } from 'react-router-dom';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { MainLayout } from '../../../components/MainLayout.jsx';
import { useAuth } from '../../../context/AuthContext.jsx';
import { renderWithProviders } from '../../helpers/renderWithProviders.jsx';

vi.mock('../../../context/AuthContext.jsx', () => ({
  useAuth: vi.fn(),
}));

describe('MainLayout', () => {
  it('renders navigation and logs out to the login route', async () => {
    const user = userEvent.setup();
    const wyloguj = vi.fn();
    useAuth.mockReturnValue({
      uzytkownik: { email: 'user@example.com' },
      wyloguj,
    });

    renderWithProviders(
      <Routes>
        <Route path="/login" element={<div>Login page</div>} />
        <Route element={<MainLayout />}>
          <Route path="/dashboard" element={<div>Dashboard content</div>} />
        </Route>
      </Routes>,
      { route: '/dashboard' }
    );

    expect(screen.getByText('AI Workfinder')).toBeInTheDocument();
    expect(screen.getByText('user@example.com')).toBeInTheDocument();
    expect(screen.getByText('Dashboard content')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Logout' }));

    expect(wyloguj).toHaveBeenCalledTimes(1);
    expect(screen.getByText('Login page')).toBeInTheDocument();
  });
});
