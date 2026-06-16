export interface ChatMessage {
  id: string;
  user_id: string;
  username: string;
  content: string;
  created_at: string;
}

export interface ChatHistoryData {
  items: ChatMessage[];
}

export interface ChatWsMessage extends ChatMessage {
  type: "message";
}

export interface ChatWsError {
  type: "error";
  message: string;
}

export type ChatWsPayload = ChatWsMessage | ChatWsError;
