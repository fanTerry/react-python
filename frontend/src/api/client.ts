import type { ApiResponse } from "../types/api";

export const API_BASE =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8999";

const TOKEN_KEY = "access_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export function isApiError<T>(
  value: T | ApiResponse<T>,
): value is ApiResponse<T> {
  return (
    typeof value === "object" &&
    value !== null &&
    "code" in value &&
    "message" in value
  );
}

export async function request<T>(
  url: string,
  options?: RequestInit,
): Promise<T | ApiResponse<T>> {
  const headers = new Headers(options?.headers);
  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(url, { ...options, headers });
  const json = await res.json();

  if (typeof json.code === "number") {
    if (json.code !== 0) return json as ApiResponse<T>;
    return json.data as T;
  }

  return {
    code: res.status,
    message: json.detail ?? json.message ?? "请求失败",
    data: null,
  } as ApiResponse<T>;
}
