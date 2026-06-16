import { API_BASE, getToken, request } from "./client";
import type { ChatHistoryData } from "../types/chat";

const API = `${API_BASE}/api/chat`;

export function fetchMessages(limit = 50) {
  return request<ChatHistoryData>(`${API}/messages?limit=${limit}`);
}

export function getChatWsUrl(): string {
  const token = getToken() ?? "";
  const query = `token=${encodeURIComponent(token)}`;

  const explicitBase = import.meta.env.VITE_API_BASE_URL;
  if (explicitBase) {
    return `${explicitBase.replace(/^http/, "ws")}/api/chat/ws?${query}`;
  }

  // Docker 生产构建：VITE_API_BASE_URL 为空，走 Nginx 同域代理
  if (import.meta.env.PROD) {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}/api/chat/ws?${query}`;
  }

  // 本地开发：与 client.ts 的 API_BASE 一致，直连后端 8999
  const wsBase = API_BASE.replace(/^http/, "ws");
  return `${wsBase}/api/chat/ws?${query}`;
}
