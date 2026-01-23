import React, { useEffect, useState } from 'react';
import { pobierzOferty } from '../api/jobs.js';
import { useI18n } from '../context/I18nContext.jsx';

function JobsListInner({ refreshToken }) {
  const { t } = useI18n();
  const [oferty, ustawOferty] = useState([]);
  const [ladowanie, ustawLadowanie] = useState(true);
  const [blad, ustawBlad] = useState(null);

  useEffect(() => {
    let aktywny = true;

    pobierzOferty()
      .then((res) => {
        if (!aktywny) return;
        ustawOferty(res.data || []);
        ustawBlad(null);
      })
      .catch((err) => {
        console.error(err);
        if (!aktywny) return;
        ustawBlad('errorLoadJobs');
      })
      .finally(() => {
        if (!aktywny) return;
        ustawLadowanie(false);
      });

    return () => {
      aktywny = false;
    };
  }, [refreshToken]);


  if (ladowanie) {
    return <div>{t('loadingJobs')}</div>;
  }

  if (blad) {
    return <div style={{ color: 'red' }}>{t(blad)}</div>;
  }

  if (!oferty.length) {
    return <div>{t('noJobs')}</div>;
  }

  const statusMap = {
    Applied: t('statusApplied'),
    'Not applied': t('statusNotApplied'),
    Failed: t('statusFailed'),
  };

  return (
    <div>
      <h2>{t('jobsTitle')}</h2>
      {oferty.map((oferta) => {
        const rawStatus = oferta.application_status
          ? oferta.application_status
          : oferta.applied
          ? 'Applied'
          : 'Not applied';
        const displayStatus = statusMap[rawStatus] || rawStatus;

        return (
          <div key={oferta._id || oferta.id || oferta.apply_url} className="card">
            <h3>{oferta.title}</h3>
            <p>
              <strong>{oferta.company}</strong> – {oferta.location}
            </p>
            <p>
              {t('sourceLabel')}: {oferta.source}
            </p>
            {oferta.relevance_score != null && (
              <p>
                {t('relevanceLabel')}: {Math.round(oferta.relevance_score * 100)}%
              </p>
            )}
            <p>
              {t('statusLabel')}: {displayStatus}
            </p>
            {oferta.apply_url && (
              <a href={oferta.apply_url} target="_blank" rel="noreferrer">
                {t('openJobPosting')}
              </a>
            )}
          </div>
        );
      })}
    </div>
  );
}

export const JobsList = React.memo(JobsListInner);
