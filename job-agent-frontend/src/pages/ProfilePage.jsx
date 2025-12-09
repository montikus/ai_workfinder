import React, { useEffect, useState, useCallback } from 'react';
import { pobierzProfil, aktualizujProfil } from '../api/auth.js';
import { klientHttp } from '../api/http.js';
import { polaczGmail } from '../api/gmail.js';
import { useAuth } from '../context/AuthContext.jsx';

export function ProfilePage() {
  const { uzytkownik, ustawUzytkownika } = useAuth();

  const [imie, ustawImie] = useState('');
  const [telefon, ustawTelefon] = useState('');
  const [lokalizacja, ustawLokalizacja] = useState('');
  const [preferencje, ustawPreferencje] = useState('');
  const [gmailPodlaczony, ustawGmailPodlaczony] = useState(false);
  const [nazwaPlikuCV, ustawNazwePlikuCV] = useState('');
  const [ladowanie, ustawLadowanie] = useState(true);
  const [zapisLadowanie, ustawZapisLadowanie] = useState(false);
  const [blad, ustawBlad] = useState(null);
  const [sukces, ustawSukces] = useState(null);

  useEffect(() => {
    let aktywny = true;
    ustawLadowanie(true);
    pobierzProfil()
      .then((res) => {
        if (!aktywny) return;
        const dane = res.data;
        ustawUzytkownika(dane);
        ustawImie(dane.name || '');
        ustawTelefon(dane.phone || '');
        ustawLokalizacja(dane.location || '');
        ustawPreferencje(dane.job_preferences_text || '');
        ustawGmailPodlaczony(!!dane.gmail_connected);
        ustawNazwePlikuCV(dane.resume_filename || '');
      })
      .catch((err) => {
        console.error(err);
        if (!aktywny) return;
        ustawBlad('Failed to load profile');
      })
      .finally(() => {
        if (!aktywny) return;
        ustawLadowanie(false);
      });

    return () => {
      aktywny = false;
    };
  }, [ustawUzytkownika]);

  const obsluzZapis = useCallback(
    async (e) => {
      e.preventDefault();
      ustawBlad(null);
      ustawSukces(null);
      ustawZapisLadowanie(true);
      try {
        const res = await aktualizujProfil({
          name: imie,
          phone: telefon,
          location: lokalizacja,
          job_preferences_text: preferencje,
        });
        ustawUzytkownika(res.data);
        ustawSukces('Profile updated');
      } catch (err) {
        console.error(err);
        ustawBlad('Failed to update profile');
      } finally {
        ustawZapisLadowanie(false);
      }
    },
    [imie, telefon, lokalizacja, preferencje, ustawUzytkownika]
  );

  const obsluzPlikCV = useCallback(async (e) => {
    const plik = e.target.files[0];
    if (!plik) return;

    const formData = new FormData();
    formData.append('resume', plik);

    try {
      await klientHttp.post('/api/upload_resume', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      ustawNazwePlikuCV(plik.name);
      ustawSukces('Resume uploaded');
    } catch (err) {
      console.error(err);
      ustawBlad('Failed to upload resume');
    }
  }, []);

  const obsluzPolaczenieGmail = useCallback(async () => {
    try {
      const res = await polaczGmail();
      const url = res.data.url;
      window.location.href = url;
    } catch (err) {
      console.error(err);
      ustawBlad('Failed to start Gmail connection');
    }
  }, []);

  if (ladowanie) {
    return <div>Loading profile...</div>;
  }

  return (
    <div>
      <h1>Profile</h1>

      {blad && <div style={{ color: 'red', marginBottom: 8 }}>{blad}</div>}
      {sukces && <div style={{ color: 'green', marginBottom: 8 }}>{sukces}</div>}

      <div className="card">
        <h2>Basic information</h2>
        <form onSubmit={obsluzZapis}>
          <input
            className="input"
            type="text"
            placeholder="Name"
            value={imie}
            onChange={(e) => ustawImie(e.target.value)}
          />
          <input
            className="input"
            type="text"
            placeholder="Phone"
            value={telefon}
            onChange={(e) => ustawTelefon(e.target.value)}
          />
          <input
            className="input"
            type="text"
            placeholder="Location"
            value={lokalizacja}
            onChange={(e) => ustawLokalizacja(e.target.value)}
          />

          <label>Job preferences (English, free text)</label>
          <textarea
            className="input"
            rows={6}
            value={preferencje}
            onChange={(e) => ustawPreferencje(e.target.value)}
          />

          <button className="button" type="submit" disabled={zapisLadowanie}>
            {zapisLadowanie ? 'Saving...' : 'Save profile'}
          </button>
        </form>
      </div>

      <div className="card">
        <h2>Resume</h2>
        <input type="file" accept=".pdf,.doc,.docx" onChange={obsluzPlikCV} />
        {nazwaPlikuCV && (
          <p style={{ marginTop: 8 }}>
            Current file: <strong>{nazwaPlikuCV}</strong>
          </p>
        )}
      </div>

      {/* <div className="card">
        <h2>Gmail</h2>
        <p>Status: {gmailPodlaczony ? 'Connected' : 'Not connected'}</p>
        {!gmailPodlaczony && (
          <button className="button" onClick={obsluzPolaczenieGmail}>
            Connect Gmail
          </button>
        )}
      </div> */}
    </div>
  );
}
