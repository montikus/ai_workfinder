import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ProfilePage } from '../../../pages/ProfilePage.jsx';
import { pobierzProfil, aktualizujProfil } from '../../../api/auth.js';
import { klientHttp } from '../../../api/http.js';
import { useAuth } from '../../../context/AuthContext.jsx';
import { renderWithProviders } from '../../helpers/renderWithProviders.jsx';

vi.mock('../../../api/auth.js', () => ({
  pobierzProfil: vi.fn(),
  aktualizujProfil: vi.fn(),
}));

vi.mock('../../../api/http.js', () => ({
  klientHttp: {
    post: vi.fn(),
  },
}));

vi.mock('../../../api/gmail.js', () => ({
  polaczGmail: vi.fn(),
}));

vi.mock('../../../context/AuthContext.jsx', () => ({
  useAuth: vi.fn(),
}));

describe('ProfilePage', () => {
  beforeEach(() => {
    pobierzProfil.mockReset();
    aktualizujProfil.mockReset();
    klientHttp.post.mockReset();
    useAuth.mockReset();
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

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
    await user.clear(screen.getByDisplayValue('+48123456789'));
    await user.type(screen.getByPlaceholderText('Phone'), '+48987654321');
    await user.clear(screen.getByDisplayValue('Warsaw'));
    await user.type(screen.getByPlaceholderText('Location'), 'Krakow');
    const preferencesInput = screen.getByDisplayValue('Remote only');
    await user.clear(preferencesInput);
    await user.type(preferencesInput, 'Hybrid');
    await user.click(screen.getByRole('button', { name: 'Save profile' }));

    await waitFor(() => {
      expect(screen.getByText('Profile updated')).toBeInTheDocument();
    });
    expect(aktualizujProfil).toHaveBeenCalledWith({
      name: 'Roman Tester',
      phone: '+48987654321',
      location: 'Krakow',
      job_preferences_text: 'Hybrid',
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

  it('rejects a resume file larger than 5 MB on the client', async () => {
    const ustawUzytkownika = vi.fn();
    useAuth.mockReturnValue({ uzytkownik: null, ustawUzytkownika });
    pobierzProfil.mockResolvedValue({ data: {} });

    const { container } = renderWithProviders(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByText('Profile')).toBeInTheDocument();
    });
    klientHttp.post.mockClear();

    const file = new File([new Uint8Array(5 * 1024 * 1024 + 1)], 'too-large.pdf', {
      type: 'application/pdf',
    });
    const input = container.querySelector('input[type="file"]');
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText('Resume file must be 5 MB or smaller.')).toBeInTheDocument();
    });
    expect(klientHttp.post).not.toHaveBeenCalled();
  });

  it('shows an error when profile loading fails', async () => {
    useAuth.mockReturnValue({ uzytkownik: null, ustawUzytkownika: vi.fn() });
    pobierzProfil.mockRejectedValue(new Error('boom'));

    renderWithProviders(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load profile')).toBeInTheDocument();
    });
  });

  it('shows an error when saving profile updates fails', async () => {
    const user = userEvent.setup();
    useAuth.mockReturnValue({ uzytkownik: null, ustawUzytkownika: vi.fn() });
    pobierzProfil.mockResolvedValue({
      data: {
        name: 'Roman',
        phone: '',
        location: '',
        job_preferences_text: '',
      },
    });
    aktualizujProfil.mockRejectedValue(new Error('boom'));

    renderWithProviders(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('Roman')).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: 'Save profile' }));

    await waitFor(() => {
      expect(screen.getByText('Failed to update profile')).toBeInTheDocument();
    });
  });

  it('shows an error when resume upload fails', async () => {
    const ustawUzytkownika = vi.fn();
    useAuth.mockReturnValue({ uzytkownik: null, ustawUzytkownika });
    pobierzProfil.mockResolvedValue({ data: {} });
    klientHttp.post.mockRejectedValue(new Error('boom'));

    const { container } = renderWithProviders(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByText('Profile')).toBeInTheDocument();
    });

    const file = new File(['resume'], 'broken-resume.pdf', { type: 'application/pdf' });
    const input = container.querySelector('input[type="file"]');
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText('Failed to upload resume')).toBeInTheDocument();
    });
  });
});
