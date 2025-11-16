import React, { useEffect, useState } from 'react';
import { pobierzOferty } from '../api/jobs.js';

function JobsListInner() {
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
      ustawBlad('Failed to load jobs');
    })
    .finally(() => {
      if (!aktywny) return;
      ustawLadowanie(false);
    });

  return () => {
    aktywny = false;
  };
}, []);


  if (ladowanie) {
    return <div>Loading jobs...</div>;
  }

  if (blad) {
    return <div style={{ color: 'red' }}>{blad}</div>;
  }

  if (!oferty.length) {
    return <div>No jobs found yet. Start a search.</div>;
  }

  return (
    <div>
      <h2>Jobs</h2>
      {oferty.map((oferta) => (
        <div key={oferta._id || oferta.id || oferta.apply_url} className="card">
          <h3>{oferta.title}</h3>
          <p>
            <strong>{oferta.company}</strong> – {oferta.location}
          </p>
          <p>Source: {oferta.source}</p>
          {oferta.relevance_score != null && (
            <p>Relevance: {Math.round(oferta.relevance_score * 100)}%</p>
          )}
          <p>
            Status:{' '}
            {oferta.application_status
              ? oferta.application_status
              : oferta.applied
              ? 'Applied'
              : 'Not applied'}
          </p>
          {oferta.apply_url && (
            <a href={oferta.apply_url} target="_blank" rel="noreferrer">
              Open job posting
            </a>
          )}
        </div>
      ))}
    </div>
  );
}

export const JobsList = React.memo(JobsListInner);
