import React, { useEffect, useState } from 'react';
import { pobierzAplikacje } from '../api/applications.js';

export function ApplicationsPage() {
  const [aplikacje, ustawAplikacje] = useState([]);
  const [ladowanie, ustawLadowanie] = useState(true);
  const [blad, ustawBlad] = useState(null);

  useEffect(() => {
    ustawLadowanie(true);
    pobierzAplikacje()
      .then((res) => {
        ustawAplikacje(res.data || []);
      })
      .catch((err) => {
        console.error(err);
        ustawBlad('Failed to load applications');
      })
      .finally(() => {
        ustawLadowanie(false);
      });
  }, []);

  if (ladowanie) {
    return <div>Loading applications...</div>;
  }

  if (blad) {
    return <div style={{ color: 'red' }}>{blad}</div>;
  }

  if (!aplikacje.length) {
    return <div>No applications yet.</div>;
  }

  return (
    <div>
      <h1>Applications</h1>
      {aplikacje.map((aplikacja) => (
        <div key={aplikacja._id || aplikacja.id} className="card">
          <h3>{aplikacja.job_title}</h3>
          <p>
            <strong>{aplikacja.company}</strong>
          </p>
          <p>Sent at: {aplikacja.sent_at}</p>
          <p>Status: {aplikacja.status}</p>
          {aplikacja.email_to && <p>To: {aplikacja.email_to}</p>}
          {aplikacja.apply_url && (
            <a href={aplikacja.apply_url} target="_blank" rel="noreferrer">
              Open job posting
            </a>
          )}
        </div>
      ))}
    </div>
  );
}
