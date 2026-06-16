import { useState } from "react";
import type { FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "../components/Layout.css";

export function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string })?.from ?? "/blog";

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  if (user) return <Navigate to={from} replace />;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const err = await login(username.trim(), password);
    if (err) {
      setError(err);
      return;
    }
    navigate(from);
  };

  return (
    <div className="app auth-page">
      <header className="header">
        <h1>登录</h1>
        <p className="subtitle">写文章需要先登录</p>
      </header>
      <form className="post-form auth-form" onSubmit={handleSubmit}>
        {error && <p className="auth-error">{error}</p>}
        <label>
          用户名
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            minLength={3}
          />
        </label>
        <label>
          密码
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
          />
        </label>
        <div className="form-actions">
          <button type="submit">登录</button>
          <Link to="/register" className="btn btn-secondary">
            去注册
          </Link>
        </div>
      </form>
    </div>
  );
}
