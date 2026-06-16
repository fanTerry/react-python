import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import { isApiError } from "../api/client";
import * as postApi from "../api/posts";
import { useAuth } from "../context/AuthContext";
import type { Post } from "../types/post";
import "../components/Layout.css";

export function BlogDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [post, setPost] = useState<Post | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    postApi.fetchPost(id).then((result) => {
      if (isApiError(result)) {
        setLoading(false);
        return;
      }
      setPost(result);
      setLoading(false);
    });
  }, [id]);

  const canManage =
    user && post?.author && post.author.id === user.id;

  const handleDelete = async () => {
    if (!id) return;
    const result = await postApi.deletePost(id);
    if (isApiError(result)) return;
    navigate("/blog");
  };

  if (loading) return <p className="status">加载中...</p>;
  if (!post) return <p className="status empty">文章不存在</p>;

  return (
    <div className="app blog-page post-detail">
      <h1>{post.title}</h1>
      <p className="post-meta">
        {post.author?.username && (
          <>
            {canManage ? (
              <Link to="/profile" className="author-link">
                {post.author.username}
              </Link>
            ) : (
              post.author.username
            )}
            {" · "}
          </>
        )}
        发布于 {new Date(post.created_at).toLocaleString()} · 更新于{" "}
        {new Date(post.updated_at).toLocaleString()}
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
      <div className="markdown-body">
        <ReactMarkdown>{post.content || "（无内容）"}</ReactMarkdown>
      </div>
      <div className="blog-actions">
        {canManage && (
          <>
            <Link to={`/blog/${post.id}/edit`} className="btn">
              编辑
            </Link>
            <button className="btn-secondary" onClick={handleDelete}>
              删除
            </button>
          </>
        )}
        <Link to="/blog" className="btn btn-secondary">
          返回列表
        </Link>
      </div>
    </div>
  );
}
