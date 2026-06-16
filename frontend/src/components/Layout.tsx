import { Link, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Layout.css";

export function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="layout">
      <nav className="nav">
        <Link to="/blog" className="nav-brand">
          博客
        </Link>
        <div className="nav-links">
          <Link to="/blog">文章</Link>
          {user ? (
            <>
              <Link to="/chat">聊天</Link>
              <button
                type="button"
                className="nav-profile-link"
                onClick={() => navigate("/profile")}
              >
                {user.username}
              </button>
              <button className="nav-logout" onClick={logout}>
                退出
              </button>
            </>
          ) : (
            <>
              <Link to="/login">登录</Link>
              <Link to="/register">注册</Link>
            </>
          )}
        </div>
      </nav>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
