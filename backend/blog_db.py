"""博客文章 SQLite 数据层（含分类、标签）。"""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from database import ensure_column, get_connection, is_postgres


def init_posts_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                category_id TEXT,
                author_id TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tags (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS post_tags (
                post_id TEXT NOT NULL,
                tag_id TEXT NOT NULL,
                PRIMARY KEY (post_id, tag_id)
            )
            """
        )
        if not is_postgres():
            ensure_column(conn, "posts", "category_id", "TEXT")
            ensure_column(conn, "posts", "author_id", "TEXT")
        ensure_column(conn, "posts", "source_url", "TEXT")
        conn.commit()


def _get_or_create_category(conn, name: str) -> str:
    row = conn.execute(
        "SELECT id FROM categories WHERE name = ?", (name,)
    ).fetchone()
    if row:
        return row["id"]
    cat_id = uuid4().hex[:8]
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO categories (id, name, created_at) VALUES (?, ?, ?)",
        (cat_id, name, now),
    )
    return cat_id


def _get_or_create_tag(conn, name: str) -> str:
    row = conn.execute("SELECT id FROM tags WHERE name = ?", (name,)).fetchone()
    if row:
        return row["id"]
    tag_id = uuid4().hex[:8]
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO tags (id, name, created_at) VALUES (?, ?, ?)",
        (tag_id, name, now),
    )
    return tag_id


def _fetch_category(conn, category_id: Optional[str]) -> Optional[dict[str, Any]]:
    if not category_id:
        return None
    row = conn.execute(
        "SELECT id, name FROM categories WHERE id = ?", (category_id,)
    ).fetchone()
    return {"id": row["id"], "name": row["name"]} if row else None


def _fetch_tags(conn, post_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT t.id, t.name FROM tags t
        JOIN post_tags pt ON pt.tag_id = t.id
        WHERE pt.post_id = ?
        ORDER BY t.name
        """,
        (post_id,),
    ).fetchall()
    return [{"id": r["id"], "name": r["name"]} for r in rows]


def _fetch_author(conn, author_id: Optional[str]) -> Optional[dict[str, Any]]:
    if not author_id:
        return None
    row = conn.execute(
        "SELECT id, username FROM users WHERE id = ?", (author_id,)
    ).fetchone()
    return {"id": row["id"], "username": row["username"]} if row else None


def _post_row_to_dict(conn, row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "content": row["content"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "category": _fetch_category(conn, row["category_id"]),
        "tags": _fetch_tags(conn, row["id"]),
        "author": _fetch_author(conn, row["author_id"]),
        "source_url": row["source_url"] if row["source_url"] else None,
    }


def list_categories() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, created_at FROM categories ORDER BY name"
        ).fetchall()
    return [{"id": r["id"], "name": r["name"], "created_at": r["created_at"]} for r in rows]


def list_tags() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, created_at FROM tags ORDER BY name"
        ).fetchall()
    return [{"id": r["id"], "name": r["name"], "created_at": r["created_at"]} for r in rows]


def list_posts(
    q: str = "",
    category_id: str = "",
    tag_id: str = "",
    author_id: str = "",
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    conditions: list[str] = []
    params: list[Any] = []

    keyword = q.strip()
    if keyword:
        conditions.append("(p.title LIKE ? OR p.content LIKE ?)")
        pattern = f"%{keyword}%"
        params.extend([pattern, pattern])

    if category_id:
        conditions.append("p.category_id = ?")
        params.append(category_id)

    if tag_id:
        conditions.append(
            "EXISTS (SELECT 1 FROM post_tags pt WHERE pt.post_id = p.id AND pt.tag_id = ?)"
        )
        params.append(tag_id)

    if author_id:
        conditions.append("p.author_id = ?")
        params.append(author_id)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    offset = (page - 1) * page_size

    with get_connection() as conn:
        total_row = conn.execute(
            f"SELECT COUNT(*) AS cnt FROM posts p {where}", params
        ).fetchone()
        rows = conn.execute(
            f"""
            SELECT p.id, p.title, p.content, p.created_at, p.updated_at,
                   p.category_id, p.author_id, p.source_url
            FROM posts p
            {where}
            ORDER BY p.created_at DESC
            LIMIT ? OFFSET ?
            """,
            [*params, page_size, offset],
        ).fetchall()
        items = [_post_row_to_dict(conn, row) for row in rows]

    return {
        "items": items,
        "total": int(total_row["cnt"] if isinstance(total_row, dict) else total_row[0]),
        "page": page,
        "page_size": page_size,
    }


def get_post(post_id: str) -> Optional[dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, title, content, created_at, updated_at, category_id, author_id, source_url
            FROM posts WHERE id = ?
            """,
            (post_id,),
        ).fetchone()
        if row is None:
            return None
        return _post_row_to_dict(conn, row)


def _set_post_tags(conn, post_id: str, tag_names: list[str]) -> None:
    conn.execute("DELETE FROM post_tags WHERE post_id = ?", (post_id,))
    for name in tag_names:
        tag = name.strip()
        if not tag:
            continue
        tag_id = _get_or_create_tag(conn, tag)
        conn.execute(
            "INSERT INTO post_tags (post_id, tag_id) VALUES (?, ?) "
            "ON CONFLICT (post_id, tag_id) DO NOTHING",
            (post_id, tag_id),
        )


def get_post_by_source_url(source_url: str) -> Optional[dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, title, content, created_at, updated_at, category_id, author_id, source_url
            FROM posts WHERE source_url = ?
            """,
            (source_url,),
        ).fetchone()
        if row is None:
            return None
        return _post_row_to_dict(conn, row)


def create_post(
    title: str,
    content: str = "",
    category_name: Optional[str] = None,
    tag_names: Optional[list[str]] = None,
    author_id: Optional[str] = None,
    source_url: Optional[str] = None,
) -> dict[str, Any]:
    post_id = uuid4().hex[:8]
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        category_id = None
        if category_name and category_name.strip():
            category_id = _get_or_create_category(conn, category_name.strip())

        conn.execute(
            """
            INSERT INTO posts (id, title, content, created_at, updated_at, category_id, author_id, source_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (post_id, title, content, now, now, category_id, author_id, source_url),
        )
        _set_post_tags(conn, post_id, tag_names or [])
        conn.commit()

    return get_post(post_id)  # type: ignore[return-value]


def update_post(
    post_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    category_name: Optional[str] = None,
    tag_names: Optional[list[str]] = None,
    category_set: bool = False,
    tags_set: bool = False,
) -> Optional[dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM posts WHERE id = ?", (post_id,)).fetchone()
        if row is None:
            return None

        updates: list[str] = []
        params: list[Any] = []

        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        if category_set:
            if category_name and category_name.strip():
                cat_id = _get_or_create_category(conn, category_name.strip())
                updates.append("category_id = ?")
                params.append(cat_id)
            else:
                updates.append("category_id = NULL")

        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.now(timezone.utc).isoformat())
            params.append(post_id)
            conn.execute(
                f"UPDATE posts SET {', '.join(updates)} WHERE id = ?",
                params,
            )

        if tags_set:
            _set_post_tags(conn, post_id, tag_names or [])

        conn.commit()

    return get_post(post_id)


def delete_post(post_id: str) -> bool:
    with get_connection() as conn:
        conn.execute("DELETE FROM post_tags WHERE post_id = ?", (post_id,))
        cursor = conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        conn.commit()
        return cursor.rowcount > 0
