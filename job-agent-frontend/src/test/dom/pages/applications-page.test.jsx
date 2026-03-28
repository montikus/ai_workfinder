import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ApplicationsPage } from '../../../pages/ApplicationsPage.jsx';
import { pobierzAplikacje } from '../../../api/applications.js';
import { renderWithProviders } from '../../helpers/renderWithProviders.jsx';

vi.mock('../../../api/applications.js', () => ({
  pobierzAplikacje: vi.fn(),
}));

describe('ApplicationsPage', () => {
  it('renders applications list', async () => {
    pobierzAplikacje.mockResolvedValue({
      data: [
        {
          id: '1',
          job_title: 'Python Developer',
          company: 'ACME',
          sent_at: '2026-03-28T12:00:00Z',
          status: 'Applied',
          email_to: 'jobs@example.com',
          apply_url: 'https://example.com/job',
        },
      ],
    });

    renderWithProviders(<ApplicationsPage />);

    await waitFor(() => {
      expect(screen.getByText('Python Developer')).toBeInTheDocument();
    });
    expect(screen.getByText(/Applied/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Open job posting' })).toHaveAttribute('href', 'https://example.com/job');
  });

  it('renders empty and error states', async () => {
    pobierzAplikacje.mockResolvedValueOnce({ data: [] });
    renderWithProviders(<ApplicationsPage />);
    await waitFor(() => {
      expect(screen.getByText('No applications yet.')).toBeInTheDocument();
    });

    pobierzAplikacje.mockRejectedValueOnce(new Error('boom'));
    renderWithProviders(<ApplicationsPage />);
    await waitFor(() => {
      expect(screen.getByText('Failed to load applications')).toBeInTheDocument();
    });
  });
});
