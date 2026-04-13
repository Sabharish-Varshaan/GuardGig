import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute({ children }) {
  const { isAuthed, role, ready } = useAuth();
  const location = useLocation();

  if (!ready) {
    return null;
  }

  if (!isAuthed || role !== 'admin') {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
}
