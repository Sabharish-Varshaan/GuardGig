import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { setAuthToken } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('guardgig_admin_token') || '');
  const [role, setRole] = useState(() => localStorage.getItem('guardgig_admin_role') || '');
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setAuthToken(token);
    setReady(true);
  }, [token]);

  const login = ({ accessToken, nextRole }) => {
    localStorage.setItem('guardgig_admin_token', accessToken);
    localStorage.setItem('guardgig_admin_role', nextRole || 'admin');
    setToken(accessToken);
    setRole(nextRole || 'admin');
    setAuthToken(accessToken);
  };

  const logout = () => {
    localStorage.removeItem('guardgig_admin_token');
    localStorage.removeItem('guardgig_admin_role');
    setToken('');
    setRole('');
    setAuthToken('');
  };

  const value = useMemo(() => ({
    token,
    role,
    ready,
    isAuthed: Boolean(token),
    login,
    logout,
  }), [token, role, ready]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }

  return context;
}
