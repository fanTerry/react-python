import { useState } from "react";
import type { FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "../components/Layout.css";

export function RegisterPage() {
  const { user, register } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  if (user) return <Navigate to="/blog" replace />;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const err = await register(
      username.trim(),
      password,
      email.trim() || undefined,
    );
    if (err) {
      setError(err);
      return;
    }
    navigate("/blog");
  };

  return (
    <div className="app auth-page">
      <header className="header">
        <h1>注册</h1>
        <p className="subtitle">创建账号后即可发布博客</p>
      </header>
      <form className="post-form auth-form" onSubmit={handleSubmit}>
        {error && <p className="auth-error">{error}</p>}
        <label>
          用户名（至少 3 位）
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            minLength={3}
          />
        </label>
        <label>
          邮箱（可选）
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <label>
          密码（至少 6 位）
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
          />
        </label>
        <div className="form-actions">
          <button type="submit">注册</button>
          <Link to="/login" className="btn btn-secondary">
            已有账号
          </Link>
        </div>
      </form>
    </div>
  );
}
