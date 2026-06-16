import { API_BASE, request } from "./client";
import type { AuthData, ProfileData, User } from "../types/auth";

const API = `${API_BASE}/api/auth`;

export function register(username: string, password: string, email?: string) {
  return request<AuthData>(`${API}/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password, email }),
  });
}

export function login(username: string, password: string) {
  return request<AuthData>(`${API}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
}

export function fetchMe() {
  return request<User>(`${API}/me`);
}

export function fetchProfile(page = 1, pageSize = 10) {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  return request<ProfileData>(`${API}/profile?${params}`);
}
