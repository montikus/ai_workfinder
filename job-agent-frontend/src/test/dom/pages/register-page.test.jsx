import React from 'react';
import { Route, Routes } from 'react-router-dom';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { RegisterPage } from '../../../pages/RegisterPage.jsx';
import { useAuth } from '../../../context/AuthContext.jsx';
import { renderWithProviders } from '../../helpers/renderWithProviders.jsx';

vi.mock('../../../context/AuthContext.jsx', () => ({
  useAuth: vi.fn(),
}));

describe('RegisterPage', () => {
  it('shows an error when passwords do not match', async () => {
    const user = userEvent.setup();
    useAuth.mockReturnValue({ zarejestruj: vi.fn() });

    renderWithProviders(
      <Routes>
        <Route path="/register" element={<RegisterPage />} />
      </Routes>,
      { route: '/register' }
    );

    await user.type(screen.getByPlaceholderText('Email'), 'user@example.com');
    await user.type(screen.getByPlaceholderText('Password'), 'Secret123!');
    await user.type(screen.getByPlaceholderText('Repeat password'), 'Different123!');
    await user.click(screen.getByRole('button', { name: 'Register' }));

    expect(screen.getByText('Passwords do not match')).toBeInTheDocument();
  });

  it('registers and navigates to login', async () => {
    const user = userEvent.setup();
    const zarejestruj = vi.fn().mockResolvedValue(undefined);
    useAuth.mockReturnValue({ zarejestruj });

    renderWithProviders(
      <Routes>
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/login" element={<div>Login page</div>} />
      </Routes>,
      { route: '/register' }
    );

    await user.type(screen.getByPlaceholderText('Email'), 'user@example.com');
    await user.type(screen.getByPlaceholderText('Password'), 'Secret123!');
    await user.type(screen.getByPlaceholderText('Repeat password'), 'Secret123!');
    await user.click(screen.getByRole('button', { name: 'Register' }));

    await waitFor(() => {
      expect(screen.getByText('Login page')).toBeInTheDocument();
    });
    expect(zarejestruj).toHaveBeenCalledWith({ email: 'user@example.com', password: 'Secret123!' });
  });

  it('shows an error when registration fails', async () => {
    const user = userEvent.setup();
    const zarejestruj = vi.fn().mockRejectedValue(new Error('failed'));
    useAuth.mockReturnValue({ zarejestruj });

    renderWithProviders(
      <Routes>
        <Route path="/register" element={<RegisterPage />} />
      </Routes>,
      { route: '/register' }
    );

    await user.type(screen.getByPlaceholderText('Email'), 'user@example.com');
    await user.type(screen.getByPlaceholderText('Password'), 'Secret123!');
    await user.type(screen.getByPlaceholderText('Repeat password'), 'Secret123!');
    await user.click(screen.getByRole('button', { name: 'Register' }));

    await waitFor(() => {
      expect(screen.getByText('Registration failed')).toBeInTheDocument();
    });
  });
});
