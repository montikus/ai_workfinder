import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import { useI18n } from '../context/I18nContext.jsx';
import { LanguageToggle } from '../components/LanguageToggle.jsx';

export function RegisterPage() {
  const { zarejestruj } = useAuth();
  const navigate = useNavigate();
  const { t } = useI18n();

  const [email, ustawEmail] = useState('');
  const [haslo, ustawHaslo] = useState('');
  const [powtorzHaslo, ustawPowtorzHaslo] = useState('');
  const [blad, ustawBlad] = useState(null);
  const [ladowanie, ustawLadowanie] = useState(false);

  const obsluzSubmit = async (e) => {
    e.preventDefault();
    ustawBlad(null);

    if (haslo !== powtorzHaslo) {
      ustawBlad('errorPasswordsMismatch');
      return;
    }
    
    ustawLadowanie(true);
    try {
      await zarejestruj({ email, password: haslo });
      navigate('/login');
    } catch (err) {
      console.error(err);
      ustawBlad('errorRegistrationFailed');
    } finally {
      ustawLadowanie(false);
    }
  };

  return (
    <>
      <div style={{ maxWidth: 400, margin: '80px auto' }}>
        <div className="card">
          <h2>{t('registerTitle')}</h2>
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
            <input
              className="input"
              type="password"
              placeholder={t('repeatPasswordPlaceholder')}
              value={powtorzHaslo}
              onChange={(e) => ustawPowtorzHaslo(e.target.value)}
              required
            />
            <button className="button" type="submit" disabled={ladowanie}>
              {ladowanie ? t('registering') : t('registerButton')}
            </button>
          </form>
          <p style={{ marginTop: 12 }}>
            {t('haveAccount')} <Link to="/login">{t('loginLink')}</Link>
          </p>
        </div>
      </div>
      <LanguageToggle className="fixed-auth" />
    </>
  );
}
