import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { isApiError } from "../api/client";
import { fetchProfile } from "../api/auth";
import type { ProfileData } from "../types/auth";
import "../components/Layout.css";

const PAGE_SIZE = 5;

export function ProfilePage() {
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const loadProfile = useCallback(async () => {
    setLoading(true);
    const result = await fetchProfile(page, PAGE_SIZE);
    if (isApiError(result)) {
      setLoading(false);
      return;
    }
    setProfile(result);
    setLoading(false);
  }, [page]);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  if (loading) return <p className="status">加载中...</p>;
  if (!profile) return <p className="status empty">无法加载个人中心</p>;

  const { user, post_count, posts } = profile;
  const totalPages = Math.max(1, Math.ceil(posts.total / PAGE_SIZE));

  return (
    <div className="app blog-page profile-page">
      <header className="header">
        <h1>个人中心</h1>
        <p className="subtitle">管理你的账号与文章</p>
      </header>

      <section className="profile-card">
        <h2>{user.username}</h2>
        <p className="profile-meta">
          {user.email ? `邮箱：${user.email} · ` : ""}
          注册于 {new Date(user.created_at).toLocaleString()}
        </p>
        <p className="profile-stats">
          已发布 <strong>{post_count}</strong> 篇文章
        </p>
        <Link to="/blog/new" className="btn">
          写新文章
        </Link>
      </section>

      <h3 className="profile-section-title">我的文章</h3>

      {posts.items.length === 0 ? (
        <p className="status empty">还没有文章，去写一篇吧</p>
      ) : (
        posts.items.map((post) => (
          <article key={post.id} className="post-card">
            <h3>
              <Link to={`/blog/${post.id}`}>{post.title}</Link>
            </h3>
            <p className="post-meta">
              更新于 {new Date(post.updated_at).toLocaleString()}
            </p>
            <div className="chip-row">
              {post.category && (
                <span className="chip chip-category">{post.category.name}</span>
              )}
              {post.tags.map((tag) => (
                <span key={tag.id} className="chip chip-tag">
                  {tag.name}
                </span>
              ))}
            </div>
            <div className="blog-actions">
              <Link to={`/blog/${post.id}/edit`} className="btn btn-secondary">
                编辑
              </Link>
            </div>
          </article>
        ))
      )}

      {posts.total > PAGE_SIZE && (
        <div className="pagination">
          <button disabled={page <= 1} onClick={() => setPage(page - 1)}>
            上一页
          </button>
          <span>
            第 {page} / {totalPages} 页
          </span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage(page + 1)}
          >
            下一页
          </button>
        </div>
      )}
    </div>
  );
}
