import { Navigate, Route, Routes } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ProtectedRoute from './components/ProtectedRoute';
import { useAuth } from './context/AuthContext';

export default function App() {
  const auth = useAuth();
  const isAdmin = auth.isAuthed && auth.role === 'admin';

  if (!auth.ready) {
    return <div className="boot-screen">Loading admin console...</div>;
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={isAdmin ? <Navigate to="/dashboard" replace /> : <LoginPage />}
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to={isAdmin ? '/dashboard' : '/login'} replace />} />
    </Routes>
  );
}
