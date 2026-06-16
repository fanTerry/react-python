import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AuthProvider } from "./context/AuthContext";
import { BlogDetailPage } from "./pages/BlogDetailPage";
import { BlogEditPage } from "./pages/BlogEditPage";
import { BlogListPage } from "./pages/BlogListPage";
import { LoginPage } from "./pages/LoginPage";
import { ProfilePage } from "./pages/ProfilePage";
import { RegisterPage } from "./pages/RegisterPage";

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/blog" replace />} />
          <Route path="blog" element={<BlogListPage />} />
          <Route path="login" element={<LoginPage />} />
          <Route path="register" element={<RegisterPage />} />
          <Route element={<ProtectedRoute />}>
            <Route path="profile" element={<ProfilePage />} />
            <Route path="blog/new" element={<BlogEditPage />} />
            <Route path="blog/:id/edit" element={<BlogEditPage />} />
          </Route>
          <Route path="blog/:id" element={<BlogDetailPage />} />
        </Route>
      </Routes>
    </AuthProvider>
  );
}

export default App;
