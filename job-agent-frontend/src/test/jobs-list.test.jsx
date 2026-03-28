import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { JobsList } from '../components/JobsList.jsx';
import { pobierzOferty } from '../api/jobs.js';
import { renderWithProviders } from './renderWithProviders.jsx';

vi.mock('../api/jobs.js', () => ({
  pobierzOferty: vi.fn(),
}));

describe('JobsList', () => {
  it('renders fetched jobs and normalizes status labels', async () => {
    pobierzOferty.mockResolvedValue({
      data: [
        {
          id: '1',
          title: 'Python Developer',
          company: 'ACME',
          location: 'Warsaw',
          source: 'justjoin',
          relevance_score: 0.89,
          applied: true,
          apply_url: 'https://example.com/job',
        },
      ],
    });

    renderWithProviders(<JobsList refreshToken="idle" />);

    await waitFor(() => {
      expect(screen.getByText('Python Developer')).toBeInTheDocument();
    });
    expect(screen.getByText(/89%/)).toBeInTheDocument();
    expect(screen.getByText(/Applied/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Open job posting' })).toHaveAttribute('href', 'https://example.com/job');
  });

  it('shows empty state when there are no jobs', async () => {
    pobierzOferty.mockResolvedValue({ data: [] });

    renderWithProviders(<JobsList refreshToken="idle" />);

    await waitFor(() => {
      expect(screen.getByText('No jobs found yet. Start a search.')).toBeInTheDocument();
    });
  });

  it('shows an error when the jobs request fails', async () => {
    pobierzOferty.mockRejectedValue(new Error('boom'));

    renderWithProviders(<JobsList refreshToken="idle" />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load jobs')).toBeInTheDocument();
    });
  });
});
