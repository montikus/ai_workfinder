import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import { useI18n } from '../context/I18nContext.jsx';
import { LanguageToggle } from '../components/LanguageToggle.jsx';

export function LoginPage() {
  const { zaloguj } = useAuth();
  const navigate = useNavigate();
  const { t } = useI18n();
  const [email, ustawEmail] = useState('');
  const [haslo, ustawHaslo] = useState('');
  const [blad, ustawBlad] = useState(null);
  const [ladowanie, ustawLadowanie] = useState(false);

  const obsluzSubmit = async (e) => {
    e.preventDefault();
    ustawBlad(null);
    ustawLadowanie(true);
    try {
      await zaloguj({ email, password: haslo });
      navigate('/dashboard');
    } catch (err) {
      console.error(err);
      ustawBlad('errorInvalidCredentials');
    } finally {
      ustawLadowanie(false);
    }
  };

  return (
    <>
      <div style={{ maxWidth: 400, margin: '80px auto' }}>
        <div className="card">
          <h2>{t('loginTitle')}</h2>
          {blad && <div style={{ color: 'red', marginBottom: 8 }}>{t(blad)}</div>}
          <form onSubmit={obsluzSubmit}>
            <input
              className="input"
              type="email"
              placeholder={t('emailPlaceholder')}
              value={email}
              onChange={(e) => ustawEmail(e.target.value)}
              required
            />
            <input
              className="input"
              type="password"
              placeholder={t('passwordPlaceholder')}
              value={haslo}
              onChange={(e) => ustawHaslo(e.target.value)}
              required
            />
            <button className="button" type="submit" disabled={ladowanie}>
              {ladowanie ? t('loggingIn') : t('loginButton')}
            </button>
          </form>
          <p style={{ marginTop: 12 }}>
            {t('noAccount')} <Link to="/register">{t('registerLink')}</Link>
          </p>
        </div>
      </div>
      <LanguageToggle className="fixed-auth" />
    </>
  );
}
