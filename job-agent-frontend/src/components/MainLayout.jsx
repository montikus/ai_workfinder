import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';

export function MainLayout() {
  const { uzytkownik, wyloguj } = useAuth();
  const navigate = useNavigate();

  const obsluzWylogowanie = () => {
    wyloguj();
    navigate('/login');
  };

  return (
    <div className="main-layout">
      <aside className="sidebar">
        <h2>Job Agent</h2>
        <nav>
          <NavLink to="/dashboard" className={({ isActive }) => (isActive ? 'active-link' : '')}>
            Dashboard
          </NavLink>
          <NavLink to="/profile" className={({ isActive }) => (isActive ? 'active-link' : '')}>
            Profile
          </NavLink>
          <NavLink to="/applications" className={({ isActive }) => (isActive ? 'active-link' : '')}>
            Applications
          </NavLink>
        </nav>
      </aside>
      <main className="main-content">
        <header className="header">
          <div>
            <strong>{uzytkownik?.email}</strong>
          </div>
          <button className="button secondary" onClick={obsluzWylogowanie}>
            Logout
          </button>
        </header>
        <Outlet />
      </main>
    </div>
  );
}
