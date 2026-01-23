import React from 'react';
import { useI18n } from '../context/I18nContext.jsx';

export function LanguageToggle({ className = '' }) {
  const { language, setLanguage, t } = useI18n();
  const nextLanguage = language === 'en' ? 'pl' : 'en';

  const handleToggle = () => {
    setLanguage(nextLanguage);
  };

  return (
    <button
      type="button"
      className={`language-toggle ${className}`.trim()}
      onClick={handleToggle}
      aria-label={t('languageLabel')}
      title={t('languageLabel')}
    >
      <span className={language === 'en' ? 'active' : ''}>EN</span>
      <span className={language === 'pl' ? 'active' : ''}>PL</span>
    </button>
  );
}
