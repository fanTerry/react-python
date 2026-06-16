export interface ChatMessage {
  id: string;
  room_id: string;
  user_id: string;
  username: string;
  content: string;
  created_at: string;
  mentions?: string[];
  read?: boolean | null;
}

export interface ChatUser {
  id: string;
  username: string;
}

export interface ChatHistoryData {
  room_id: string;
  items: ChatMessage[];
}

export interface DmRoom {
  room_id: string;
  peer: ChatUser;
}

export interface ChatRoomsData {
  public_room: string;
  dm_rooms: DmRoom[];
  online_count: number;
  online_users: ChatUser[];
  unread_mentions?: number;
}

export interface MentionItem {
  message_id: string;
  room_id: string;
  from_user: ChatUser;
  content: string;
  created_at: string;
}

export interface UnreadMentionsData {
  count: number;
  items: MentionItem[];
}

export interface ChatWsMessage extends ChatMessage {
  type: "message";
}

export interface ChatWsPresence {
  type: "presence";
  online_count: number;
  users: ChatUser[];
}

export interface ChatWsJoined {
  type: "joined";
  room_id: string;
  online_count?: number;
  users?: ChatUser[];
  unread_mentions?: number;
}

export interface ChatWsRead {
  type: "read";
  room_id: string;
  user_id: string;
  username: string;
  last_read_at: string;
}

export interface ChatWsMention {
  type: "mention";
  message: ChatMessage;
  from_user: ChatUser;
}

export interface ChatWsError {
  type: "error";
  message: string;
}

export type ChatWsPayload =
  | ChatWsMessage
  | ChatWsPresence
  | ChatWsJoined
  | ChatWsRead
  | ChatWsMention
  | ChatWsError;

export const PUBLIC_ROOM = "public";

export function dmRoomId(userIdA: string, userIdB: string): string {
  const [a, b] = [userIdA, userIdB].sort();
  return `dm:${a}:${b}`;
}

export function roomLabel(roomId: string): string {
  return roomId === PUBLIC_ROOM ? "公共大厅" : "私聊";
}
