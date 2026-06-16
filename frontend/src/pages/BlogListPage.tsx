import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { isApiError } from "../api/client";
import * as postApi from "../api/posts";
import { useAuth } from "../context/AuthContext";
import type { Category, Post, Tag } from "../types/post";
import "../components/Layout.css";

const PAGE_SIZE = 5;

export function BlogListPage() {
  const { user } = useAuth();
  const [posts, setPosts] = useState<Post[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [keyword, setKeyword] = useState("");
  const [search, setSearch] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [tagId, setTagId] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    postApi.fetchCategories().then((r) => {
      if (!isApiError(r)) setCategories(r ?? []);
    });
    postApi.fetchTags().then((r) => {
      if (!isApiError(r)) setTags(r ?? []);
    });
  }, []);

  const loadPosts = useCallback(async () => {
    setLoading(true);
    const result = await postApi.fetchPosts({
      q: search,
      category_id: categoryId,
      tag_id: tagId,
      page,
      page_size: PAGE_SIZE,
    });
    if (isApiError(result)) {
      setLoading(false);
      return;
    }
    setPosts(result?.items ?? []);
    setTotal(result?.total ?? 0);
    setLoading(false);
  }, [search, categoryId, tagId, page]);

  useEffect(() => {
    loadPosts();
  }, [loadPosts]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const handleSearch = () => {
    setSearch(keyword);
    setPage(1);
  };

  const handleDelete = async (id: string) => {
    const result = await postApi.deletePost(id);
    if (isApiError(result)) return;
    loadPosts();
  };

  const canManage = (post: Post) =>
    user && post.author && post.author.id === user.id;

  return (
    <div className="app blog-page">
      <header className="header">
        <h1>博客</h1>
        <p className="subtitle">Markdown · 分类 · 标签 · JWT 登录</p>
      </header>

      <div className="blog-toolbar">
        <input
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          placeholder="搜索标题或内容..."
        />
        <button onClick={handleSearch}>搜索</button>
        {user ? (
          <Link to="/blog/new" className="btn">
            写文章
          </Link>
        ) : (
          <Link to="/login" className="btn">
            登录后写作
          </Link>
        )}
      </div>

      <div className="filter-bar">
        <select
          value={categoryId}
          onChange={(e) => {
            setCategoryId(e.target.value);
            setPage(1);
          }}
        >
          <option value="">全部分类</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        <select
          value={tagId}
          onChange={(e) => {
            setTagId(e.target.value);
            setPage(1);
          }}
        >
          <option value="">全部标签</option>
          {tags.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <p className="status">加载中...</p>
      ) : posts.length === 0 ? (
        <p className="status empty">暂无文章</p>
      ) : (
        posts.map((post) => (
          <article key={post.id} className="post-card">
            <h3>
              <Link to={`/blog/${post.id}`}>{post.title}</Link>
            </h3>
            <p className="post-meta">
              {post.author?.username && (
                <>
                  {canManage(post) ? (
                    <Link to="/profile" className="author-link">
                      {post.author.username}
                    </Link>
                  ) : (
                    post.author.username
                  )}
                  {" · "}
                </>
              )}
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
            <p className="post-excerpt">
              {post.content.slice(0, 120) || "（无内容）"}
              {post.content.length > 120 ? "..." : ""}
            </p>
            {canManage(post) && (
              <div className="blog-actions">
                <Link to={`/blog/${post.id}/edit`} className="btn btn-secondary">
                  编辑
                </Link>
                <button className="btn-secondary" onClick={() => handleDelete(post.id)}>
                  删除
                </button>
              </div>
            )}
          </article>
        ))
      )}

      <div className="pagination">
        <button disabled={page <= 1} onClick={() => setPage(page - 1)}>
          上一页
        </button>
        <span>
          第 {page} / {totalPages} 页（共 {total} 篇）
        </span>
        <button disabled={page >= totalPages} onClick={() => setPage(page + 1)}>
          下一页
        </button>
      </div>
    </div>
  );
}
