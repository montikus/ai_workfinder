import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';

export function ProtectedRoute() {
  const { zalogowany, ladowanie } = useAuth();

  if (ladowanie) {
    return <div>Loading...</div>;
  }

  if (!zalogowany) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
