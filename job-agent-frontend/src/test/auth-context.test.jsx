import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { AuthProvider, useAuth } from '../context/AuthContext.jsx';
import { logowanie, pobierzProfil, rejestracja } from '../api/auth.js';
import { renderWithProviders } from './renderWithProviders.jsx';

vi.mock('../api/auth.js', () => ({
  logowanie: vi.fn(),
  rejestracja: vi.fn(),
  pobierzProfil: vi.fn(),
}));

function AuthConsumer() {
  const {
    uzytkownik,
    token,
    zalogowany,
    ladowanie,
    zaloguj,
    zarejestruj,
    wyloguj,
  } = useAuth();

  return (
    <div>
      <div data-testid="email">{uzytkownik?.email || ''}</div>
      <div data-testid="token">{token || ''}</div>
      <div data-testid="logged">{String(zalogowany)}</div>
      <div data-testid="loading">{String(ladowanie)}</div>
      <button type="button" onClick={() => zaloguj({ email: 'user@example.com', password: 'Secret123!' })}>
        login
      </button>
      <button type="button" onClick={() => zarejestruj({ email: 'user@example.com', password: 'Secret123!' })}>
        register
      </button>
      <button type="button" onClick={wyloguj}>
        logout
      </button>
    </div>
  );
}

describe('AuthContext', () => {
  it('finishes loading without a stored token', async () => {
    renderWithProviders(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false');
    });
    expect(screen.getByTestId('logged')).toHaveTextContent('false');
  });

  it('loads the current profile when a token exists and clears invalid tokens', async () => {
    localStorage.setItem('token', 'stored-token');
    pobierzProfil.mockResolvedValueOnce({ data: { email: 'user@example.com' } });

    const firstRender = renderWithProviders(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('email')).toHaveTextContent('user@example.com');
    });
    expect(screen.getByTestId('logged')).toHaveTextContent('true');

    firstRender.unmount();

    localStorage.setItem('token', 'broken-token');
    pobierzProfil.mockRejectedValueOnce(new Error('unauthorized'));

    renderWithProviders(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false');
      expect(screen.getByTestId('logged')).toHaveTextContent('false');
      expect(screen.getByTestId('email')).toHaveTextContent('');
      expect(localStorage.getItem('token')).toBeNull();
    });
  });

  it('logs in, registers, and logs out', async () => {
    const user = userEvent.setup();
    logowanie.mockResolvedValue({
      data: {
        token: 'new-token',
        user: { email: 'user@example.com' },
      },
    });
    rejestracja.mockResolvedValue({ data: { message: 'ok' } });

    renderWithProviders(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false');
    });

    await user.click(screen.getByRole('button', { name: 'register' }));
    expect(rejestracja).toHaveBeenCalledWith({ email: 'user@example.com', password: 'Secret123!' });

    await user.click(screen.getByRole('button', { name: 'login' }));
    await waitFor(() => {
      expect(screen.getByTestId('email')).toHaveTextContent('user@example.com');
    });
    expect(localStorage.getItem('token')).toBe('new-token');

    await user.click(screen.getByRole('button', { name: 'logout' }));
    expect(screen.getByTestId('logged')).toHaveTextContent('false');
    expect(localStorage.getItem('token')).toBeNull();
  });
});
