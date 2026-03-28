import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { ProfilePage } from '../pages/ProfilePage.jsx';
import { pobierzProfil, aktualizujProfil } from '../api/auth.js';
import { klientHttp } from '../api/http.js';
import { useAuth } from '../context/AuthContext.jsx';
import { renderWithProviders } from './renderWithProviders.jsx';

vi.mock('../api/auth.js', () => ({
  pobierzProfil: vi.fn(),
  aktualizujProfil: vi.fn(),
}));

vi.mock('../api/http.js', () => ({
  klientHttp: {
    post: vi.fn(),
  },
}));

vi.mock('../api/gmail.js', () => ({
  polaczGmail: vi.fn(),
}));

vi.mock('../context/AuthContext.jsx', () => ({
  useAuth: vi.fn(),
}));

describe('ProfilePage', () => {
  it('loads the profile and saves updates', async () => {
    const user = userEvent.setup();
    const ustawUzytkownika = vi.fn();
    useAuth.mockReturnValue({ uzytkownik: null, ustawUzytkownika });
    pobierzProfil.mockResolvedValue({
      data: {
        name: 'Roman',
        phone: '+48123456789',
        location: 'Warsaw',
        job_preferences_text: 'Remote only',
        gmail_connected: false,
        resume_filename: 'resume.pdf',
      },
    });
    aktualizujProfil.mockResolvedValue({
      data: {
        name: 'Roman Tester',
        phone: '+48123456789',
        location: 'Warsaw',
        job_preferences_text: 'Remote only',
      },
    });

    renderWithProviders(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('Roman')).toBeInTheDocument();
    });
    expect(screen.getByText(/Current file/i)).toHaveTextContent('resume.pdf');

    await user.clear(screen.getByDisplayValue('Roman'));
    await user.type(screen.getByPlaceholderText('Name'), 'Roman Tester');
    await user.click(screen.getByRole('button', { name: 'Save profile' }));

    await waitFor(() => {
      expect(screen.getByText('Profile updated')).toBeInTheDocument();
    });
    expect(aktualizujProfil).toHaveBeenCalledWith({
      name: 'Roman Tester',
      phone: '+48123456789',
      location: 'Warsaw',
      job_preferences_text: 'Remote only',
    });
    expect(ustawUzytkownika).toHaveBeenCalled();
  });

  it('uploads a resume file and shows success state', async () => {
    const ustawUzytkownika = vi.fn();
    useAuth.mockReturnValue({ uzytkownik: null, ustawUzytkownika });
    pobierzProfil.mockResolvedValue({ data: {} });
    klientHttp.post.mockResolvedValue({ data: { resume_filename: 'fresh-resume.pdf' } });

    const { container } = renderWithProviders(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByText('Profile')).toBeInTheDocument();
    });

    const file = new File(['resume'], 'fresh-resume.pdf', { type: 'application/pdf' });
    const input = container.querySelector('input[type="file"]');
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText('Resume uploaded')).toBeInTheDocument();
    });
    expect(screen.getByText(/Current file/i)).toHaveTextContent('fresh-resume.pdf');
    expect(klientHttp.post).toHaveBeenCalled();
    expect(ustawUzytkownika).toHaveBeenCalledTimes(1);
  });

  it('shows an error when profile loading fails', async () => {
    useAuth.mockReturnValue({ uzytkownik: null, ustawUzytkownika: vi.fn() });
    pobierzProfil.mockRejectedValue(new Error('boom'));

    renderWithProviders(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load profile')).toBeInTheDocument();
    });
  });
});
