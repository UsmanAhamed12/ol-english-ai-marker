import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./../components/layout/Layout.jsx";
import ProtectedRoute from "./../components/common/ProtectedRoute.jsx";
import Dashboard from "./../pages/Dashboard.jsx";
import Knowledge from "./../pages/Knowledge.jsx";
import Login from "./../pages/Login.jsx";
import NewPaper from "./../pages/NewPaper.jsx";
import PaperDetail from "./../pages/PaperDetail.jsx";
import Papers from "./../pages/Papers.jsx";
import Register from "./../pages/Register.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/papers" element={<Papers />} />
          <Route path="/papers/:paperId" element={<PaperDetail />} />
          <Route path="/new" element={<NewPaper />} />
          <Route path="/knowledge" element={<Knowledge />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}