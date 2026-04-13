import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { DashboardPage } from '../../../pages/DashboardPage.jsx';
import { pobierzProfil } from '../../../api/auth.js';
import { pobierzStatusWyszukiwania, rozpocznijWyszukiwanie } from '../../../api/jobs.js';
import { renderWithProviders } from '../../helpers/renderWithProviders.jsx';

vi.mock('../../../api/auth.js', () => ({
  pobierzProfil: vi.fn(),
}));

vi.mock('../../../api/jobs.js', () => ({
  rozpocznijWyszukiwanie: vi.fn(),
  pobierzStatusWyszukiwania: vi.fn(),
}));

vi.mock('../../../components/JobsList.jsx', () => ({
  JobsList: ({ refreshToken }) => <div data-testid="jobs-list">{refreshToken}</div>,
}));

function makeStreamResponse(chunks) {
  const encoder = new TextEncoder();
  let index = 0;

  return {
    ok: true,
    body: {
      getReader() {
        return {
          async read() {
            if (index >= chunks.length) {
              return { done: true, value: undefined };
            }
            const value = encoder.encode(chunks[index]);
            index += 1;
            return { done: false, value };
          },
        };
      },
    },
  };
}

describe('DashboardPage', () => {
  beforeEach(() => {
    pobierzProfil.mockReset();
    pobierzStatusWyszukiwania.mockReset();
    rozpocznijWyszukiwanie.mockReset();
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  it('loads profile data and validates search input', async () => {
    const user = userEvent.setup();
    pobierzProfil.mockResolvedValue({
      data: {
        name: 'Roman',
        location: 'Warsaw',
        job_preferences_text: 'Remote only',
        resume_filename: 'resume.pdf',
      },
    });
    pobierzStatusWyszukiwania.mockResolvedValue({ data: { status: 'idle' } });

    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('Remote only')).toBeInTheDocument();
    });

    const specializationInput = screen.getByPlaceholderText('python, javascript, devops, ai...');
    await user.clear(specializationInput);
    await user.click(screen.getByRole('button', { name: 'Start search' }));

    expect(screen.getByText('Specialization is required.')).toBeInTheDocument();
    expect(screen.getByTestId('jobs-list')).toHaveTextContent('idle-');
  });

  it('starts search and consumes stream updates', async () => {
    const user = userEvent.setup();
    localStorage.setItem('token', 'token-123');
    pobierzProfil.mockResolvedValue({
      data: {
        name: 'Roman',
        location: 'Warsaw',
        job_preferences_text: 'Remote only',
        resume_filename: 'resume.pdf',
      },
    });
    pobierzStatusWyszukiwania.mockResolvedValue({ data: { status: 'idle' } });
    rozpocznijWyszukiwanie.mockResolvedValue({ data: { status: 'running' } });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      makeStreamResponse([
        'event: log\ndata: {"ts":"2026-03-28T12:00:00Z","level":"INFO","message":"AI search started"}\n\n' +
          'event: status\ndata: {"status":"finished","jobs_found":1,"total_one_click":1,"applied_ok":1,"attempted_apply":1,"error":null,"finished_at":"2026-03-28T12:01:00Z"}\n\n' +
          'event: done\ndata: {}\n\n',
      ])
    ));

    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('Roman')).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: 'Start search' }));

    await waitFor(() => {
      expect(rozpocznijWyszukiwanie).toHaveBeenCalledWith({
        specialization: 'python',
        experience_level: null,
        location: 'Warsaw',
        limit: 20,
        max_apply: 3,
        full_name: 'Roman',
        user_request: 'Remote only',
      });
    });

    await waitFor(() => {
      expect(fetch).toHaveBeenCalled();
    });
    await waitFor(() => {
      expect(screen.getByText(/AI search started/)).toBeInTheDocument();
    });
    expect(screen.getByText('Jobs found: 1 | One-click jobs: 1')).toBeInTheDocument();
    expect(screen.getByText('Applied: 1 / 1 (successful / attempted)')).toBeInTheDocument();
    expect(screen.getByTestId('jobs-list')).toHaveTextContent('finished-2026-03-28T12:01:00Z');
  });

  it('validates missing full name and missing resume requirements', async () => {
    const user = userEvent.setup();
    pobierzProfil.mockResolvedValue({
      data: {
        name: '',
        location: 'Warsaw',
        job_preferences_text: '',
        resume_filename: '',
      },
    });
    pobierzStatusWyszukiwania.mockResolvedValue({ data: { status: 'idle' } });

    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('No job preferences set yet. Go to Profile and add them.')).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: 'Start search' }));
    expect(screen.getByText('Full name is required.')).toBeInTheDocument();

    await user.type(screen.getByPlaceholderText('Full name'), 'Roman Tester');
    await user.click(screen.getByRole('button', { name: 'Start search' }));

    expect(screen.getByText('Please upload your resume in Profile first.')).toBeInTheDocument();
  });

  it('validates numeric inputs and shows an error when starting the search fails', async () => {
    const user = userEvent.setup();
    pobierzProfil.mockResolvedValue({
      data: {
        name: 'Roman',
        location: 'Warsaw',
        job_preferences_text: '',
        resume_filename: 'resume.pdf',
      },
    });
    pobierzStatusWyszukiwania.mockResolvedValue({ data: { status: 'idle' } });
    rozpocznijWyszukiwanie.mockRejectedValue(new Error('boom'));

    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('Roman')).toBeInTheDocument();
    });

    const experienceSelect = screen.getByRole('combobox');
    const [limitInput, maxApplyInput] = screen.getAllByRole('spinbutton');
    const locationInput = screen.getByPlaceholderText('warszawa, krakow, all-locations');

    await user.selectOptions(experienceSelect, 'senior');
    await user.clear(locationInput);
    await user.type(locationInput, '   ');

    fireEvent.change(limitInput, { target: { value: '0' } });
    await user.click(screen.getByRole('button', { name: 'Start search' }));
    expect(screen.getByText('Limit must be between 1 and 100.')).toBeInTheDocument();

    fireEvent.change(limitInput, { target: { value: '20' } });
    fireEvent.change(maxApplyInput, { target: { value: '101' } });
    await user.click(screen.getByRole('button', { name: 'Start search' }));
    expect(screen.getByText('Max apply must be between 1 and 100.')).toBeInTheDocument();

    fireEvent.change(maxApplyInput, { target: { value: '3' } });
    await user.click(screen.getByRole('button', { name: 'Start search' }));

    await waitFor(() => {
      expect(rozpocznijWyszukiwanie).toHaveBeenCalledWith({
        specialization: 'python',
        experience_level: 'senior',
        location: null,
        limit: 20,
        max_apply: 3,
        full_name: 'Roman',
        user_request: null,
      });
    });
    expect(screen.getByText('Failed to start search')).toBeInTheDocument();
  });

  it('shows stream errors and backend status details when the stream disconnects', async () => {
    localStorage.setItem('token', 'token-123');
    pobierzProfil.mockResolvedValue({
      data: {
        name: 'Roman',
        location: 'Warsaw',
        job_preferences_text: '',
        resume_filename: 'resume.pdf',
      },
    });
    pobierzStatusWyszukiwania.mockResolvedValue({
      data: {
        status: 'running',
        jobs_found: 2,
        total_one_click: 1,
        applied_ok: 0,
        attempted_apply: 1,
        error: 'backend boom',
      },
    });
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        body: null,
      })
    );

    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('Last error: backend boom')).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.getByText('Stream disconnected')).toBeInTheDocument();
    });
    expect(screen.getByText('Search in progress...')).toBeDisabled();
  });
});
