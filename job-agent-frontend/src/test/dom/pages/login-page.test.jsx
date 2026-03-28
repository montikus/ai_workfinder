import React from 'react';
import { Route, Routes } from 'react-router-dom';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { LoginPage } from '../../../pages/LoginPage.jsx';
import { useAuth } from '../../../context/AuthContext.jsx';
import { renderWithProviders } from '../../helpers/renderWithProviders.jsx';

vi.mock('../../../context/AuthContext.jsx', () => ({
  useAuth: vi.fn(),
}));

describe('LoginPage', () => {
  it('logs in and navigates to the dashboard', async () => {
    const user = userEvent.setup();
    const zaloguj = vi.fn().mockResolvedValue(undefined);
    useAuth.mockReturnValue({ zaloguj });

    renderWithProviders(
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/dashboard" element={<div>Dashboard page</div>} />
      </Routes>,
      { route: '/login' }
    );

    await user.type(screen.getByPlaceholderText('Email'), 'user@example.com');
    await user.type(screen.getByPlaceholderText('Password'), 'Secret123!');
    await user.click(screen.getByRole('button', { name: 'Login' }));

    await waitFor(() => {
      expect(screen.getByText('Dashboard page')).toBeInTheDocument();
    });
    expect(zaloguj).toHaveBeenCalledWith({ email: 'user@example.com', password: 'Secret123!' });
  });

  it('shows an error when login fails', async () => {
    const user = userEvent.setup();
    const zaloguj = vi.fn().mockRejectedValue(new Error('bad credentials'));
    useAuth.mockReturnValue({ zaloguj });

    renderWithProviders(
      <Routes>
        <Route path="/login" element={<LoginPage />} />
      </Routes>,
      { route: '/login' }
    );

    await user.type(screen.getByPlaceholderText('Email'), 'user@example.com');
    await user.type(screen.getByPlaceholderText('Password'), 'Secret123!');
    await user.click(screen.getByRole('button', { name: 'Login' }));

    await waitFor(() => {
      expect(screen.getByText('Invalid email or password')).toBeInTheDocument();
    });
  });
});
