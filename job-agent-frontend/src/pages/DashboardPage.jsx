import React, { useEffect, useState } from 'react';
import { pobierzProfil } from '../api/auth.js';
import { rozpocznijWyszukiwanie, pobierzStatusWyszukiwania } from '../api/jobs.js';
import { JobsList } from '../components/JobsList.jsx';

export function DashboardPage() {
  const [preferencje, ustawPreferencje] = useState('');
  const [status, ustawStatus] = useState('idle'); // idle | running | finished | failed
  const [statystyki, ustawStatystyki] = useState(null);
  const [blad, ustawBlad] = useState(null);
  const [ladowanie, ustawLadowanie] = useState(true);

  useEffect(() => {
    // загружаем профиль, чтобы показать job_preferences_text
    pobierzProfil()
      .then((res) => {
        ustawPreferencje(res.data.job_preferences_text || '');
      })
      .catch((err) => {
        console.error(err);
      })
      .finally(() => {
        ustawLadowanie(false);
      });

    // загружаем текущий статус поиска (если есть)
    pobierzStatusWyszukiwania()
      .then((res) => {
        if (res.data && res.data.status) {
          ustawStatus(res.data.status);
          ustawStatystyki(res.data);
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    let intervalId;

    if (status === 'running') {
      intervalId = setInterval(() => {
        pobierzStatusWyszukiwania()
          .then((res) => {
            ustawStatus(res.data.status);
            ustawStatystyki(res.data);
          })
          .catch((err) => {
            console.error(err);
            ustawStatus('failed');
            ustawBlad('Failed to load search status');
          });
      }, 5000);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [status]);

  const obsluzStartWyszukiwania = async () => {
    ustawBlad(null);
    try {
      await rozpocznijWyszukiwanie();
      ustawStatus('running');
    } catch (err) {
      console.error(err);
      ustawBlad('Failed to start search');
    }
  };

  return (
    <div>
      <h1>Dashboard</h1>
      {ladowanie ? (
        <div>Loading...</div>
      ) : (
        <>
          <div className="card">
            <h2>Job preferences</h2>
            {preferencje ? (
              <pre style={{ whiteSpace: 'pre-wrap' }}>{preferencje}</pre>
            ) : (
              <p>No job preferences set yet. Go to Profile and add them.</p>
            )}
          </div>

          <div className="card">
            <h2>Search jobs</h2>
            {blad && <div style={{ color: 'red', marginBottom: 8 }}>{blad}</div>}
            <p>
              Status:{' '}
              <strong>
                {status === 'idle' && 'Not started'}
                {status === 'running' && 'Running'}
                {status === 'finished' && 'Finished'}
                {status === 'failed' && 'Failed'}
              </strong>
            </p>
            {statystyki && (
              <p>
                Jobs found: {statystyki.jobs_found} | Applications sent: {statystyki.applications_sent}
              </p>
            )}
            <button
              className="button"
              onClick={obsluzStartWyszukiwania}
              disabled={status === 'running'}
            >
              {status === 'running' ? 'Search in progress...' : 'Start search'}
            </button>
          </div>

          <JobsList />
        </>
      )}
    </div>
  );
}
