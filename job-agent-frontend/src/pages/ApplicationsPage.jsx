import React, { useEffect, useState } from 'react';
import { pobierzAplikacje } from '../api/applications.js';
import { useI18n } from '../context/I18nContext.jsx';

export function ApplicationsPage() {
  const { t } = useI18n();
  const [aplikacje, ustawAplikacje] = useState([]);
  const [ladowanie, ustawLadowanie] = useState(true);
  const [blad, ustawBlad] = useState(null);

  useEffect(() => {
    let aktywny = true;

    pobierzAplikacje()
      .then((res) => {
        if (!aktywny) return;
        ustawAplikacje(res.data || []);
        ustawBlad(null);
      })
      .catch((err) => {
        if (!aktywny) return;
        console.error(err);
        ustawBlad('errorLoadApplications');
      })
      .finally(() => {
        if (!aktywny) return;
        ustawLadowanie(false);
      });

    return () => {
      aktywny = false;
    };
  }, []);

  const statusMap = {
    Applied: t('statusApplied'),
    'Not applied': t('statusNotApplied'),
    Failed: t('statusFailed'),
  };

  if (ladowanie) {
    return <div>{t('loadingApplications')}</div>;
  }

  if (blad) {
    return <div style={{ color: 'red' }}>{t(blad)}</div>;
  }

  if (!aplikacje.length) {
    return <div>{t('noApplications')}</div>;
  }

  return (
    <div>
      <h1>{t('applicationsTitle')}</h1>
      {aplikacje.map((aplikacja) => {
        const displayStatus = statusMap[aplikacja.status] || aplikacja.status;
        return (
          <div key={aplikacja._id || aplikacja.id} className="card">
            <h3>{aplikacja.job_title}</h3>
            <p>
              <strong>{aplikacja.company}</strong>
            </p>
            <p>
              {t('sentAtLabel')}: {aplikacja.sent_at}
            </p>
            <p>
              {t('statusLabel')}: {displayStatus}
            </p>
            {aplikacja.email_to && (
              <p>
                {t('toLabel')}: {aplikacja.email_to}
              </p>
            )}
            {aplikacja.apply_url && (
              <a href={aplikacja.apply_url} target="_blank" rel="noreferrer">
                {t('openJobPosting')}
              </a>
            )}
          </div>
        );
      })}
    </div>
  );
}
