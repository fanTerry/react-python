import { Fragment, useCallback, useEffect, useRef, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import {
  fetchMessages,
  fetchRooms,
  fetchUnreadMentions,
  getChatWsUrl,
  markMentionsRead,
} from "../api/chat";
import { getToken, isApiError } from "../api/client";
import { useAuth } from "../context/AuthContext";
import type {
  ChatMessage,
  ChatUser,
  ChatWsPayload,
  DmRoom,
  MentionItem,
} from "../types/chat";
import { dmRoomId, PUBLIC_ROOM, roomLabel } from "../types/chat";
import "../components/Layout.css";

type ActiveRoom =
  | { kind: "public" }
  | { kind: "dm"; peer: ChatUser; roomId: string };

const MENTION_SPLIT = /(@\w{3,32})/g;

function roomTitle(room: ActiveRoom): string {
  if (room.kind === "public") return "公共大厅";
  return `私聊 · ${room.peer.username}`;
}

function renderMessageContent(content: string): ReactNode[] {
  return content.split(MENTION_SPLIT).map((part, index) => {
    if (part.startsWith("@")) {
      return (
        <span key={`${part}-${index}`} className="chat-mention">
          {part}
        </span>
      );
    }
    return <Fragment key={`text-${index}`}>{part}</Fragment>;
  });
}

function notifyMentionsUpdated() {
  window.dispatchEvent(new Event("mentions-updated"));
}

export function ChatPage() {
  const { user } = useAuth();
  const [activeRoom, setActiveRoom] = useState<ActiveRoom>({ kind: "public" });
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [dmRooms, setDmRooms] = useState<DmRoom[]>([]);
  const [onlineUsers, setOnlineUsers] = useState<ChatUser[]>([]);
  const [onlineCount, setOnlineCount] = useState(0);
  const [mentionAlerts, setMentionAlerts] = useState<MentionItem[]>([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState<"connecting" | "open" | "closed">(
    "connecting",
  );
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const listRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const seenIds = useRef(new Set<string>());
  const activeRoomIdRef = useRef(PUBLIC_ROOM);
  const userIdRef = useRef<string | null>(null);

  userIdRef.current = user?.id ?? null;

  const currentRoomId =
    activeRoom.kind === "public" ? PUBLIC_ROOM : activeRoom.roomId;

  activeRoomIdRef.current = currentRoomId;

  const resetMessages = useCallback((items: ChatMessage[]) => {
    seenIds.current = new Set(items.map((m) => m.id));
    setMessages(items);
  }, []);

  const appendMessage = useCallback((msg: ChatMessage) => {
    if (msg.room_id !== activeRoomIdRef.current) return;
    if (seenIds.current.has(msg.id)) return;
    seenIds.current.add(msg.id);
    setMessages((prev) => [...prev, msg]);
  }, []);

  const sendReadReceipt = useCallback((roomId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "read", room_id: roomId }));
    }
  }, []);

  const loadMentionAlerts = useCallback(async () => {
    const result = await fetchUnreadMentions();
    if (isApiError(result)) return;
    setMentionAlerts(result.items);
  }, []);

  const loadRoomHistory = useCallback(
    async (roomId: string) => {
      setLoading(true);
      const result = await fetchMessages(roomId);
      if (isApiError(result)) {
        setError(result.message);
        setLoading(false);
        return;
      }
      resetMessages(result.items);
      setLoading(false);
      sendReadReceipt(roomId);
    },
    [resetMessages, sendReadReceipt],
  );

  const refreshRooms = useCallback(async () => {
    const result = await fetchRooms();
    if (isApiError(result)) return;
    setDmRooms(result.dm_rooms);
    setOnlineCount(result.online_count);
    setOnlineUsers(result.online_users);
  }, []);

  const joinRoom = useCallback((roomId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "join", room_id: roomId }));
    }
  }, []);

  const selectPublic = useCallback(() => {
    setActiveRoom({ kind: "public" });
    setError("");
    joinRoom(PUBLIC_ROOM);
    loadRoomHistory(PUBLIC_ROOM);
  }, [joinRoom, loadRoomHistory]);

  const selectDm = useCallback(
    (peer: ChatUser) => {
      if (!user || peer.id === user.id) return;
      const roomId = dmRoomId(user.id, peer.id);
      setActiveRoom({ kind: "dm", peer, roomId });
      setError("");
      joinRoom(roomId);
      loadRoomHistory(roomId);
    },
    [joinRoom, loadRoomHistory, user],
  );

  const openMention = useCallback(
    async (item: MentionItem) => {
      await markMentionsRead([item.message_id]);
      notifyMentionsUpdated();
      setMentionAlerts((prev) =>
        prev.filter((m) => m.message_id !== item.message_id),
      );

      if (item.room_id === PUBLIC_ROOM) {
        selectPublic();
        return;
      }

      const parts = item.room_id.split(":");
      if (parts.length !== 3 || !user) return;
      const peerId = parts[1] === user.id ? parts[2] : parts[1];
      const peer =
        item.from_user.id === peerId
          ? item.from_user
          : onlineUsers.find((u) => u.id === peerId) ??
            dmRooms.find((r) => r.peer.id === peerId)?.peer;

      if (peer) {
        selectDm(peer);
      }
    },
    [dmRooms, onlineUsers, selectDm, selectPublic, user],
  );

  const insertMention = useCallback((username: string) => {
    setInput((prev) => {
      const prefix = prev.endsWith(" ") || prev === "" ? "" : " ";
      return `${prev}${prefix}@${username} `;
    });
  }, []);

  useEffect(() => {
    loadRoomHistory(PUBLIC_ROOM);
    loadMentionAlerts();
  }, [loadMentionAlerts, loadRoomHistory]);

  useEffect(() => {
    refreshRooms();
  }, [refreshRooms]);

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
      ws.send(
        JSON.stringify({ type: "join", room_id: activeRoomIdRef.current }),
      );
    };
    ws.onclose = () => setStatus("closed");
    ws.onerror = () =>
      setError("WebSocket 连接失败，请确认后端已启动（8999 端口）");
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data) as ChatWsPayload;
      if (data.type === "error") {
        setError(data.message);
        return;
      }
      if (data.type === "presence") {
        setOnlineCount(data.online_count);
        setOnlineUsers(data.users);
        return;
      }
      if (data.type === "joined") {
        if (data.online_count !== undefined) {
          setOnlineCount(data.online_count);
        }
        if (data.users) {
          setOnlineUsers(data.users);
        }
        return;
      }
      if (data.type === "read") {
        const roomId = activeRoomIdRef.current;
        if (roomId.startsWith("dm:") && userIdRef.current) {
          const parts = roomId.split(":");
          const peerId =
            parts[1] === userIdRef.current ? parts[2] : parts[1];
          if (data.user_id === peerId) {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.user_id === userIdRef.current
                  ? { ...msg, read: true }
                  : msg,
              ),
            );
          }
        }
        return;
      }
      if (data.type === "mention") {
        if (data.message.room_id !== activeRoomIdRef.current) {
          setMentionAlerts((prev) => {
            if (prev.some((m) => m.message_id === data.message.id)) {
              return prev;
            }
            return [
              {
                message_id: data.message.id,
                room_id: data.message.room_id,
                from_user: data.from_user,
                content: data.message.content,
                created_at: data.message.created_at,
              },
              ...prev,
            ];
          });
        } else {
          sendReadReceipt(activeRoomIdRef.current);
          markMentionsRead([data.message.id]).then(() => notifyMentionsUpdated());
        }
        return;
      }
      appendMessage(data);
      if (data.user_id !== userIdRef.current) {
        sendReadReceipt(activeRoomIdRef.current);
      }
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [appendMessage, sendReadReceipt]);

  useEffect(() => {
    listRef.current?.scrollTo({
      top: listRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const content = input.trim();
    if (
      !content ||
      !wsRef.current ||
      wsRef.current.readyState !== WebSocket.OPEN
    ) {
      return;
    }
    wsRef.current.send(JSON.stringify({ content }));
    setInput("");
    setError("");
  };

  const otherOnlineUsers = onlineUsers.filter((u) => u.id !== user?.id);

  return (
    <div className="app chat-page">
      <header className="header">
        <h1>聊天室</h1>
        <p className="subtitle">
          {roomTitle(activeRoom)} · 在线 {onlineCount} 人
          {status === "open" && " · 已连接"}
          {status === "connecting" && " · 连接中..."}
          {status === "closed" && " · 已断开"}
        </p>
      </header>

      {error && <p className="auth-error">{error}</p>}

      {mentionAlerts.length > 0 && (
        <div className="chat-mention-alerts">
          {mentionAlerts.map((item) => (
            <button
              key={item.message_id}
              type="button"
              className="chat-mention-alert"
              onClick={() => openMention(item)}
            >
              <strong>{item.from_user.username}</strong> 在
              {roomLabel(item.room_id)} @了你：
              {item.content.slice(0, 40)}
              {item.content.length > 40 ? "..." : ""}
            </button>
          ))}
        </div>
      )}

      <div className="chat-layout">
        <aside className="chat-sidebar">
          <button
            type="button"
            className={
              activeRoom.kind === "public"
                ? "chat-room-btn active"
                : "chat-room-btn"
            }
            onClick={selectPublic}
          >
            公共大厅
          </button>

          <p className="chat-sidebar-title">
            在线用户 ({otherOnlineUsers.length})
          </p>
          {otherOnlineUsers.length === 0 ? (
            <p className="chat-sidebar-empty">暂无其他在线用户</p>
          ) : (
            otherOnlineUsers.map((u) => (
              <div key={u.id} className="chat-user-row">
                <button
                  type="button"
                  className={
                    activeRoom.kind === "dm" && activeRoom.peer.id === u.id
                      ? "chat-room-btn active"
                      : "chat-room-btn"
                  }
                  onClick={() => selectDm(u)}
                >
                  {u.username}
                </button>
                <button
                  type="button"
                  className="chat-mention-btn"
                  title={`@${u.username}`}
                  onClick={() => insertMention(u.username)}
                >
                  @
                </button>
              </div>
            ))
          )}

          {dmRooms.length > 0 && (
            <>
              <p className="chat-sidebar-title">历史私聊</p>
              {dmRooms.map((room) => (
                <button
                  key={room.room_id}
                  type="button"
                  className={
                    activeRoom.kind === "dm" &&
                    activeRoom.roomId === room.room_id
                      ? "chat-room-btn active"
                      : "chat-room-btn"
                  }
                  onClick={() => selectDm(room.peer)}
                >
                  {room.peer.username}
                </button>
              ))}
            </>
          )}
        </aside>

        <section className="chat-main">
          {loading ? (
            <p className="status">加载中...</p>
          ) : (
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
                      <span>
                        {new Date(msg.created_at).toLocaleString()}
                        {activeRoom.kind === "dm" &&
                          msg.user_id === user?.id &&
                          msg.read !== null &&
                          msg.read !== undefined && (
                            <em className="chat-read-badge">
                              {msg.read ? " · 已读" : " · 未读"}
                            </em>
                          )}
                      </span>
                    </div>
                    <p className="chat-message-content">
                      {renderMessageContent(msg.content)}
                    </p>
                  </div>
                ))
              )}
            </div>
          )}

          <form className="chat-form" onSubmit={handleSubmit}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={
                activeRoom.kind === "public"
                  ? "公共大厅说点什么，输入 @用户名 提醒对方..."
                  : `私信 ${activeRoom.peer.username}...`
              }
              maxLength={2000}
              disabled={status !== "open" || loading}
            />
            <button
              type="submit"
              disabled={status !== "open" || loading || !input.trim()}
            >
              发送
            </button>
          </form>
        </section>
      </div>
    </div>
  );
}
