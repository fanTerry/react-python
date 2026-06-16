import { useCallback, useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { fetchMessages, getChatWsUrl } from "../api/chat";
import { getToken, isApiError } from "../api/client";
import { useAuth } from "../context/AuthContext";
import type { ChatMessage, ChatWsPayload } from "../types/chat";
import "../components/Layout.css";

export function ChatPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState<"connecting" | "open" | "closed">(
    "connecting",
  );
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const listRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const seenIds = useRef(new Set<string>());

  const appendMessage = useCallback((msg: ChatMessage) => {
    if (seenIds.current.has(msg.id)) return;
    seenIds.current.add(msg.id);
    setMessages((prev) => [...prev, msg]);
  }, []);

  useEffect(() => {
    let cancelled = false;

    fetchMessages().then((result) => {
      if (cancelled) return;
      if (isApiError(result)) {
        setError(result.message);
        setLoading(false);
        return;
      }
      for (const msg of result.items) {
        seenIds.current.add(msg.id);
      }
      setMessages(result.items);
      setLoading(false);
    });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!getToken()) {
      setError("请先登录后再进入聊天室");
      setStatus("closed");
      setLoading(false);
      return;
    }

    const ws = new WebSocket(getChatWsUrl());
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("open");
      setError("");
    };
    ws.onclose = () => setStatus("closed");
    ws.onerror = () => setError("WebSocket 连接失败，请确认后端已启动（8999 端口）");
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data) as ChatWsPayload;
      if (data.type === "error") {
        setError(data.message);
        return;
      }
      appendMessage(data);
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [appendMessage]);

  useEffect(() => {
    listRef.current?.scrollTo({
      top: listRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const content = input.trim();
    if (!content || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return;
    }
    wsRef.current.send(JSON.stringify({ content }));
    setInput("");
    setError("");
  };

  if (loading) return <p className="status">加载中...</p>;

  return (
    <div className="app chat-page">
      <header className="header">
        <h1>聊天室</h1>
        <p className="subtitle">
          WebSocket 实时消息 · 登录用户：{user?.username}
          {status === "open" && " · 已连接"}
          {status === "connecting" && " · 连接中..."}
          {status === "closed" && " · 已断开"}
        </p>
      </header>

      {error && <p className="auth-error">{error}</p>}

      <div className="chat-messages" ref={listRef}>
        {messages.length === 0 ? (
          <p className="status empty">还没有消息，发第一条吧</p>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={
                msg.user_id === user?.id
                  ? "chat-message chat-message-own"
                  : "chat-message"
              }
            >
              <div className="chat-message-meta">
                <strong>{msg.username}</strong>
                <span>{new Date(msg.created_at).toLocaleString()}</span>
              </div>
              <p className="chat-message-content">{msg.content}</p>
            </div>
          ))
        )}
      </div>

      <form className="chat-form" onSubmit={handleSubmit}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="输入消息，Enter 发送..."
          maxLength={2000}
          disabled={status !== "open"}
        />
        <button type="submit" disabled={status !== "open" || !input.trim()}>
          发送
        </button>
      </form>
    </div>
  );
}
