import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import { useI18n } from '../context/I18nContext.jsx';
import { LanguageToggle } from './LanguageToggle.jsx';

export function MainLayout() {
  const { uzytkownik, wyloguj } = useAuth();
  const { t } = useI18n();
  const navigate = useNavigate();

  const obsluzWylogowanie = () => {
    wyloguj();
    navigate('/login');
  };

  return (
    <div className="main-layout">
      <aside className="sidebar">
        <h2>{t('appTitle')}</h2>
        <nav className="sidebar-nav">
          <NavLink to="/dashboard" className={({ isActive }) => (isActive ? 'active-link' : '')}>
            {t('navDashboard')}
          </NavLink>
          <NavLink to="/profile" className={({ isActive }) => (isActive ? 'active-link' : '')}>
            {t('navProfile')}
          </NavLink>
          <NavLink to="/applications" className={({ isActive }) => (isActive ? 'active-link' : '')}>
            {t('navApplications')}
          </NavLink>
        </nav>
        <div className="sidebar-footer">
          <LanguageToggle />
        </div>
      </aside>
      <main className="main-content">
        <header className="header">
          <div>
            <strong>{uzytkownik?.email}</strong>
          </div>
          <button className="button secondary" onClick={obsluzWylogowanie}>
            {t('logout')}
          </button>
        </header>
        <Outlet />
      </main>
    </div>
  );
}
