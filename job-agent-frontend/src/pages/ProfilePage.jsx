import React, { useEffect, useState, useCallback } from 'react';
import { pobierzProfil, aktualizujProfil } from '../api/auth.js';
import { klientHttp } from '../api/http.js';
import { polaczGmail } from '../api/gmail.js';
import { useAuth } from '../context/AuthContext.jsx';
import { useI18n } from '../context/I18nContext.jsx';

export function ProfilePage() {
  const { uzytkownik, ustawUzytkownika } = useAuth();
  const { t } = useI18n();

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
        ustawBlad('errorLoadProfile');
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
        ustawSukces('profileUpdated');
      } catch (err) {
        console.error(err);
        ustawBlad('errorUpdateProfile');
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
      const res = await klientHttp.post('/api/upload_resume', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      ustawNazwePlikuCV(res.data?.resume_filename || plik.name);
      ustawSukces('resumeUploaded');
    } catch (err) {
      console.error(err);
      ustawBlad('errorUploadResume');
    }
  }, []);

  const obsluzPolaczenieGmail = useCallback(async () => {
    try {
      const res = await polaczGmail();
      const url = res.data.url;
      window.location.href = url;
    } catch (err) {
      console.error(err);
      ustawBlad('errorGmailConnect');
    }
  }, []);

  if (ladowanie) {
    return <div>{t('loadingProfile')}</div>;
  }

  return (
    <div>
      <h1>{t('profileTitle')}</h1>

      {blad && <div style={{ color: 'red', marginBottom: 8 }}>{t(blad)}</div>}
      {sukces && <div style={{ color: 'green', marginBottom: 8 }}>{t(sukces)}</div>}

      <div className="card">
        <h2>{t('basicInfoTitle')}</h2>
        <form onSubmit={obsluzZapis}>
          <input
            className="input"
            type="text"
            placeholder={t('namePlaceholder')}
            value={imie}
            onChange={(e) => ustawImie(e.target.value)}
          />
          <input
            className="input"
            type="text"
            placeholder={t('phonePlaceholder')}
            value={telefon}
            onChange={(e) => ustawTelefon(e.target.value)}
          />
          <input
            className="input"
            type="text"
            placeholder={t('locationLabel')}
            value={lokalizacja}
            onChange={(e) => ustawLokalizacja(e.target.value)}
          />

          <label>{t('preferencesLabel')}</label>
          <textarea
            className="input"
            rows={6}
            value={preferencje}
            onChange={(e) => ustawPreferencje(e.target.value)}
          />

          <button className="button" type="submit" disabled={zapisLadowanie}>
            {zapisLadowanie ? t('saving') : t('saveProfile')}
          </button>
        </form>
      </div>

      <div className="card">
        <h2>{t('resumeTitle')}</h2>
        <input type="file" accept=".pdf,.doc,.docx" onChange={obsluzPlikCV} />
        {nazwaPlikuCV && (
          <p style={{ marginTop: 8 }}>
            {t('currentFileLabel')}: <strong>{nazwaPlikuCV}</strong>
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
