import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const navigate = useNavigate();
  const auth = useAuth();
  const [email, setEmail] = useState('admin@guardgig.com');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await api.post('/api/admin/login', { email, password });
      auth.login({ accessToken: response.data.access_token, nextRole: response.data.role });
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(err?.response?.data?.detail || 'Invalid admin credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-shell">
      <div className="orb orb-one" />
      <div className="orb orb-two" />
      <div className="auth-card">
        <div className="eyebrow">GuardGig Admin</div>
        <h1>Secure dashboard access</h1>
        <p>Sign in with the seeded admin account to review actuarial metrics.</p>

        <form onSubmit={submit} className="form">
          <label>
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="admin@guardgig.com"
              autoComplete="email"
              required
            />
          </label>

          <label>
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
              required
            />
          </label>

          {error ? <div className="error-banner">{error}</div> : null}

          <button type="submit" className="primary-btn" disabled={loading}>
            {loading ? 'Signing in...' : 'Login'}
          </button>
        </form>

        <div className="helper-text">
          Admin only. Normal user tokens are blocked from the dashboard.
        </div>
      </div>
    </div>
  );
}
