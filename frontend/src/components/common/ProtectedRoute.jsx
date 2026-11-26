import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "./../../hooks/useAuth.jsx";

export default function ProtectedRoute() {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="grid min-h-screen place-items-center">
        <p className="text-sm text-inkSoft">Loading your studio…</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}