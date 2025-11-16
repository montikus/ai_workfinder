import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';

export function RegisterPage() {
  const { zarejestruj } = useAuth();
  const navigate = useNavigate();

  const [email, ustawEmail] = useState('');
  const [haslo, ustawHaslo] = useState('');
  const [powtorzHaslo, ustawPowtorzHaslo] = useState('');
  const [blad, ustawBlad] = useState(null);
  const [ladowanie, ustawLadowanie] = useState(false);

  const obsluzSubmit = async (e) => {
    e.preventDefault();
    ustawBlad(null);

    if (haslo !== powtorzHaslo) {
      ustawBlad('Passwords do not match');
      return;
    }
    
    ustawLadowanie(true);
    try {
      console.log(haslo)
      await zarejestruj({ email, password: haslo });
      navigate('/login');
    } catch (err) {
      console.error(err);
      ustawBlad('Registration failed');
    } finally {
      ustawLadowanie(false);
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: '80px auto' }}>
      <div className="card">
        <h2>Register</h2>
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
          <input
            className="input"
            type="password"
            placeholder="Repeat password"
            value={powtorzHaslo}
            onChange={(e) => ustawPowtorzHaslo(e.target.value)}
            required
          />
          <button className="button" type="submit" disabled={ladowanie}>
            {ladowanie ? 'Registering...' : 'Register'}
          </button>
        </form>
        <p style={{ marginTop: 12 }}>
          Already have an account? <Link to="/login">Login</Link>
        </p>
      </div>
    </div>
  );
}
