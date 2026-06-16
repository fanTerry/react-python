import { useEffect, useState } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { fetchUnreadMentions } from "../api/chat";
import { isApiError } from "../api/client";
import { useAuth } from "../context/AuthContext";
import "./Layout.css";

export function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mentionCount, setMentionCount] = useState(0);

  useEffect(() => {
    if (!user) {
      setMentionCount(0);
      return;
    }
    const refresh = () => {
      fetchUnreadMentions().then((result) => {
        if (!isApiError(result)) {
          setMentionCount(result.count);
        }
      });
    };
    refresh();
    window.addEventListener("mentions-updated", refresh);
    return () => window.removeEventListener("mentions-updated", refresh);
  }, [user, location.pathname]);

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
              <Link to="/chat" className="nav-chat-link">
                聊天
                {mentionCount > 0 && (
                  <span className="nav-badge">{mentionCount}</span>
                )}
              </Link>
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
