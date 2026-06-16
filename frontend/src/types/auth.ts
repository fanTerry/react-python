import type { PostListData } from "./post";

export interface User {
  id: string;
  username: string;
  email: string | null;
  created_at: string;
}

export interface AuthData {
  access_token: string;
  user: User;
}

export interface ProfileData {
  user: User;
  post_count: number;
  posts: PostListData;
}
