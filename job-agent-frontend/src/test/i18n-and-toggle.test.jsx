import React from 'react';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { LanguageProvider, useI18n } from '../context/I18nContext.jsx';
import { LanguageToggle } from '../components/LanguageToggle.jsx';
import { renderWithProviders } from './renderWithProviders.jsx';

function I18nConsumer() {
  const { language, setLanguage, t } = useI18n();

  return (
    <div>
      <div data-testid="language">{language}</div>
      <div>{t('statsJobsFound', { jobs: 2, oneClick: 1 })}</div>
      <div>{t('missing-key')}</div>
      <button type="button" onClick={() => setLanguage('pl')}>
        set-pl
      </button>
    </div>
  );
}

describe('i18n', () => {
  it('uses english by default and falls back to the key for missing translations', () => {
    renderWithProviders(
      <LanguageProvider>
        <I18nConsumer />
      </LanguageProvider>
    );

    expect(screen.getByTestId('language')).toHaveTextContent('en');
    expect(screen.getByText('Jobs found: 2 | One-click jobs: 1')).toBeInTheDocument();
    expect(screen.getByText('missing-key')).toBeInTheDocument();
  });

  it('persists language changes and toggles with LanguageToggle', async () => {
    localStorage.setItem('language', 'pl');
    const user = userEvent.setup();

    renderWithProviders(
      <LanguageProvider>
        <I18nConsumer />
        <LanguageToggle />
      </LanguageProvider>
    );

    expect(screen.getByTestId('language')).toHaveTextContent('pl');
    expect(screen.getByText('Znalezione: 2 | 1-click: 1')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Język' }));

    expect(screen.getByTestId('language')).toHaveTextContent('en');
    expect(localStorage.getItem('language')).toBe('en');
  });
});
