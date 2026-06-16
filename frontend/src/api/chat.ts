import { API_BASE, getToken, request } from "./client";
import type { ChatHistoryData, ChatRoomsData, UnreadMentionsData } from "../types/chat";

const API = `${API_BASE}/api/chat`;

export function fetchMessages(roomId: string, limit = 50) {
  const params = new URLSearchParams({
    room_id: roomId,
    limit: String(limit),
  });
  return request<ChatHistoryData>(`${API}/messages?${params}`);
}

export function fetchRooms() {
  return request<ChatRoomsData>(`${API}/rooms`);
}

export function fetchUnreadMentions(limit = 20) {
  return request<UnreadMentionsData>(`${API}/mentions/unread?limit=${limit}`);
}

export function markMentionsRead(messageIds?: string[]) {
  return request<{ marked: number }>(`${API}/mentions/read`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message_ids: messageIds ?? null }),
  });
}

export function getChatWsUrl(): string {
  const token = getToken() ?? "";
  const query = `token=${encodeURIComponent(token)}`;

  const explicitBase = import.meta.env.VITE_API_BASE_URL;
  if (explicitBase) {
    return `${explicitBase.replace(/^http/, "ws")}/api/chat/ws?${query}`;
  }

  if (import.meta.env.PROD) {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}/api/chat/ws?${query}`;
  }

  const wsBase = API_BASE.replace(/^http/, "ws");
  return `${wsBase}/api/chat/ws?${query}`;
}
