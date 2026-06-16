import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { isApiError } from "../api/client";
import * as postApi from "../api/posts";
import "../components/Layout.css";

export function BlogEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEdit = Boolean(id);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [categoryName, setCategoryName] = useState("");
  const [tagInput, setTagInput] = useState("");
  const [loading, setLoading] = useState(isEdit);

  useEffect(() => {
    if (!id) return;
    postApi.fetchPost(id).then((result) => {
      if (isApiError(result)) {
        setLoading(false);
        return;
      }
      setTitle(result.title);
      setContent(result.content);
      setCategoryName(result.category?.name ?? "");
      setTagInput(result.tags.map((t) => t.name).join(", "));
      setLoading(false);
    });
  }, [id]);

  const parseTags = () =>
    tagInput
      .split(/[,，]/)
      .map((t) => t.trim())
      .filter(Boolean);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const trimmedTitle = title.trim();
    if (!trimmedTitle) return;

    const payload = {
      title: trimmedTitle,
      content,
      category_name: categoryName.trim() || undefined,
      tag_names: parseTags(),
    };

    if (isEdit && id) {
      const result = await postApi.updatePost(id, payload);
      if (isApiError(result)) return;
      navigate(`/blog/${id}`);
    } else {
      const result = await postApi.createPost(payload);
      if (isApiError(result)) return;
      navigate(`/blog/${result.id}`);
    }
  };

  if (loading) return <p className="status">加载中...</p>;

  return (
    <div className="app blog-page">
      <header className="header">
        <h1>{isEdit ? "编辑文章" : "写文章"}</h1>
        <p className="subtitle">支持 Markdown · 分类 · 标签</p>
      </header>

      <form className="post-form" onSubmit={handleSubmit}>
        <label>
          标题
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="输入标题"
            required
          />
        </label>
        <label>
          分类
          <input
            value={categoryName}
            onChange={(e) => setCategoryName(e.target.value)}
            placeholder="例如：技术、生活（不存在会自动创建）"
          />
        </label>
        <label>
          标签（逗号分隔）
          <input
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            placeholder="Python, FastAPI, 学习笔记"
          />
        </label>
        <label>
          内容（Markdown）
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="# 标题&#10;&#10;在这里写 Markdown..."
          />
        </label>
        <div className="form-actions">
          <button type="submit">保存</button>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => navigate(isEdit && id ? `/blog/${id}` : "/blog")}
          >
            取消
          </button>
        </div>
      </form>
    </div>
  );
}
