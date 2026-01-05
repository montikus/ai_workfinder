import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';

export function LoginPage() {
  const { zaloguj } = useAuth();
  const navigate = useNavigate();
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
      ustawBlad('Nieprawidłowy email lub hasło');
    } finally {
      ustawLadowanie(false);
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: '80px auto' }}>
      <div className="card">
        <h2>Login</h2>
        {blad && <div style={{ color: 'red', marginBottom: 8 }}>{blad}</div>}
        <form onSubmit={obsluzSubmit}>
          <input
            className="input"
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => ustawEmail(e.target.value)}
            required
          />
          <input
            className="input"
            type="password"
            placeholder="Password"
            value={haslo}
            onChange={(e) => ustawHaslo(e.target.value)}
            required
          />
          <button className="button" type="submit" disabled={ladowanie}>
            {ladowanie ? 'Logging in...' : 'Login'}
          </button>
        </form>
        <p style={{ marginTop: 12 }}>
          No account? <Link to="/register">Register</Link>
        </p>
      </div>
    </div>
  );
}
