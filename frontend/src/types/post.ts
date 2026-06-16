export interface Category {
  id: string;
  name: string;
  created_at: string;
}

export interface Tag {
  id: string;
  name: string;
  created_at: string;
}

export interface PostAuthor {
  id: string;
  username: string;
}

export interface Post {
  id: string;
  title: string;
  content: string;
  created_at: string;
  updated_at: string;
  category: Category | null;
  tags: Tag[];
  author: PostAuthor | null;
}

export interface PostListData {
  items: Post[];
  total: number;
  page: number;
  page_size: number;
}

export interface PostQuery {
  q: string;
  category_id: string;
  tag_id: string;
  page: number;
  page_size: number;
}

export interface PostPayload {
  title: string;
  content: string;
  category_name?: string;
  tag_names?: string[];
}
