import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import { useI18n } from '../context/I18nContext.jsx';

export function ProtectedRoute() {
  const { zalogowany, ladowanie } = useAuth();
  const { t } = useI18n();

  if (ladowanie) {
    return <div>{t('loading')}</div>;
  }

  if (!zalogowany) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
