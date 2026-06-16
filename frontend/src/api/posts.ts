import { API_BASE, request } from "./client";
import type { Category, Post, PostListData, PostPayload, PostQuery, Tag } from "../types/post";

const API = `${API_BASE}/api/posts`;

export function buildPostListUrl(query: PostQuery): string {
  const params = new URLSearchParams({
    page: String(query.page),
    page_size: String(query.page_size),
  });
  if (query.q.trim()) params.set("q", query.q.trim());
  if (query.category_id) params.set("category_id", query.category_id);
  if (query.tag_id) params.set("tag_id", query.tag_id);
  return `${API}?${params}`;
}

export function fetchPosts(query: PostQuery) {
  return request<PostListData>(buildPostListUrl(query));
}

export function fetchPost(id: string) {
  return request<Post>(`${API}/${id}`);
}

export function fetchCategories() {
  return request<Category[]>(`${API}/meta/categories`);
}

export function fetchTags() {
  return request<Tag[]>(`${API}/meta/tags`);
}

export function createPost(data: PostPayload) {
  return request<Post>(API, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function updatePost(id: string, data: Partial<PostPayload>) {
  return request<Post>(`${API}/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function deletePost(id: string) {
  return request<null>(`${API}/${id}`, { method: "DELETE" });
}
