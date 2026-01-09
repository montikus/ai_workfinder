import React, { useCallback, useEffect, useRef, useState } from 'react';
import { pobierzProfil } from '../api/auth.js';
import { rozpocznijWyszukiwanie, pobierzStatusWyszukiwania } from '../api/jobs.js';
import { JobsList } from '../components/JobsList.jsx';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

export function DashboardPage() {
  const [profil, ustawProfil] = useState(null);
  const [preferencje, ustawPreferencje] = useState('');
  const [specjalizacja, ustawSpecjalizacje] = useState('python');
  const [doswiadczenie, ustawDoswiadczenie] = useState('');
  const [lokalizacja, ustawLokalizacje] = useState('');
  const [limit, ustawLimit] = useState(20);
  const [maxAplikacji, ustawMaxAplikacji] = useState(3);
  const [pelneImie, ustawPelneImie] = useState('');
  const [status, ustawStatus] = useState('idle'); // idle | running | finished | failed
  const [statystyki, ustawStatystyki] = useState(null);
  const [blad, ustawBlad] = useState(null);
  const [bladStreamu, ustawBladStreamu] = useState(null);
  const [logi, ustawLogi] = useState([]);
  const [ladowanie, ustawLadowanie] = useState(true);
  const streamControllerRef = useRef(null);

  useEffect(() => {
    // загружаем профиль, чтобы показать job_preferences_text
    pobierzProfil()
      .then((res) => {
        const dane = res.data;
        ustawProfil(dane);
        ustawPreferencje(dane.job_preferences_text || '');
        ustawPelneImie((wartosc) => wartosc || dane.name || '');
        ustawLokalizacje((wartosc) => wartosc || dane.location || '');
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

  const zakonczStream = useCallback(() => {
    if (streamControllerRef.current) {
      streamControllerRef.current.abort();
      streamControllerRef.current = null;
    }
  }, []);

  const rozpocznijStream = useCallback(() => {
    if (streamControllerRef.current) return;

    const token = localStorage.getItem('token');
    if (!token) return;

    const controller = new AbortController();
    streamControllerRef.current = controller;
    ustawBladStreamu(null);

    const run = async () => {
      const res = await fetch(`${API_BASE_URL}/api/search_stream`, {
        headers: { Authorization: `Bearer ${token}` },
        signal: controller.signal,
      });

      if (!res.ok || !res.body) {
        throw new Error('Stream request failed');
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split('\n\n');
        buffer = chunks.pop() || '';

        for (const chunk of chunks) {
          const lines = chunk.split('\n');
          let eventType = 'message';
          const dataLines = [];

          for (const line of lines) {
            if (line.startsWith('event:')) {
              eventType = line.slice(6).trim();
            } else if (line.startsWith('data:')) {
              dataLines.push(line.slice(5).trim());
            }
          }

          if (!dataLines.length) continue;
          const rawData = dataLines.join('\n');
          let parsed = rawData;
          try {
            parsed = JSON.parse(rawData);
          } catch (_) {}

          if (eventType === 'status' && parsed && parsed.status) {
            ustawStatus(parsed.status);
            ustawStatystyki(parsed);
          } else if (eventType === 'log') {
            ustawLogi((poprzednie) => [...poprzednie, parsed]);
          } else if (eventType === 'done') {
            controller.abort();
            return;
          }
        }
      }
    };

    run()
      .catch((err) => {
        if (err.name === 'AbortError') return;
        console.error(err);
        ustawBladStreamu('Stream disconnected');
      })
      .finally(() => {
        streamControllerRef.current = null;
      });
  }, []);

  useEffect(() => {
    if (status === 'running') {
      rozpocznijStream();
      return;
    }
    zakonczStream();
  }, [status, rozpocznijStream, zakonczStream]);

  useEffect(() => {
    return () => {
      zakonczStream();
    };
  }, [zakonczStream]);

  const obsluzStartWyszukiwania = async () => {
    ustawBlad(null);
    ustawBladStreamu(null);
    ustawLogi([]);
    const specjalizacjaTrim = specjalizacja.trim();
    const pelneImieTrim = pelneImie.trim();
    const limitNum = Number(limit);
    const maxApplyNum = Number(maxAplikacji);

    if (!specjalizacjaTrim) {
      ustawBlad('Specialization is required.');
      return;
    }
    if (!pelneImieTrim) {
      ustawBlad('Full name is required.');
      return;
    }
    if (!profil?.resume_filename) {
      ustawBlad('Please upload your resume in Profile first.');
      return;
    }
    if (!Number.isFinite(limitNum) || limitNum < 1 || limitNum > 100) {
      ustawBlad('Limit must be between 1 and 100.');
      return;
    }
    if (!Number.isFinite(maxApplyNum) || maxApplyNum < 1 || maxApplyNum > 100) {
      ustawBlad('Max apply must be between 1 and 100.');
      return;
    }

    try {
      await rozpocznijWyszukiwanie({
        specialization: specjalizacjaTrim,
        experience_level: doswiadczenie || null,
        location: lokalizacja.trim() || null,
        limit: limitNum,
        max_apply: maxApplyNum,
        full_name: pelneImieTrim,
        user_request: preferencje || null,
      });
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
            <label>Specialization</label>
            <input
              className="input"
              type="text"
              placeholder="python, javascript, devops, ai..."
              value={specjalizacja}
              onChange={(e) => ustawSpecjalizacje(e.target.value)}
            />
            <label>Experience level</label>
            <select
              className="input"
              value={doswiadczenie}
              onChange={(e) => ustawDoswiadczenie(e.target.value)}
            >
              <option value="">Any</option>
              <option value="junior">Junior</option>
              <option value="mid">Mid</option>
              <option value="senior">Senior</option>
              <option value="c-level">C-level</option>
            </select>
            <label>Location</label>
            <input
              className="input"
              type="text"
              placeholder="warszawa, krakow, all-locations"
              value={lokalizacja}
              onChange={(e) => ustawLokalizacje(e.target.value)}
            />
            <label>Results limit</label>
            <input
              className="input"
              type="number"
              min="1"
              max="100"
              value={limit}
              onChange={(e) => ustawLimit(e.target.value)}
            />
            <label>Max applications</label>
            <input
              className="input"
              type="number"
              min="1"
              max="100"
              value={maxAplikacji}
              onChange={(e) => ustawMaxAplikacji(e.target.value)}
            />
            <label>Full name</label>
            <input
              className="input"
              type="text"
              placeholder="Full name"
              value={pelneImie}
              onChange={(e) => ustawPelneImie(e.target.value)}
            />
            <p style={{ marginTop: 8 }}>
              Resume: <strong>{profil?.resume_filename || 'Not uploaded'}</strong>
            </p>
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
              <>
                <p>
                  Jobs found: {statystyki.jobs_found} | One-click jobs: {statystyki.total_one_click}
                </p>
                <p>
                  Applied: {statystyki.applied_ok} / {statystyki.attempted_apply} (successful / attempted)
                </p>
              </>
            )}
            {statystyki?.error && <div className="status-error">Last error: {statystyki.error}</div>}
            <button
              className="button"
              onClick={obsluzStartWyszukiwania}
              disabled={status === 'running'}
            >
              {status === 'running' ? 'Search in progress...' : 'Start search'}
            </button>
          </div>

          <div className="card">
            <h2>Agent stream</h2>
            {bladStreamu && <div className="status-error">{bladStreamu}</div>}
            {logi.length ? (
              <div
                style={{
                  maxHeight: 260,
                  overflowY: 'auto',
                  fontFamily: 'monospace',
                  fontSize: 12,
                  whiteSpace: 'pre-wrap',
                }}
              >
                {logi.map((log, index) => (
                  <div key={`${log?.ts || 'log'}-${index}`}>
                    {log?.ts ? `[${log.ts}] ` : ''}
                    {log?.level ? `${log.level} ` : ''}
                    {log?.message || log}
                  </div>
                ))}
              </div>
            ) : (
              <p>No stream messages yet.</p>
            )}
          </div>

          <JobsList refreshToken={`${status}-${statystyki?.finished_at || ''}`} />
        </>
      )}
    </div>
  );
}
