"""聊天消息 SQLite 数据层。"""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from database import get_connection


def init_chat_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                username TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _row_to_dict(row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "username": row["username"],
        "content": row["content"],
        "created_at": row["created_at"],
    }


def create_message(user_id: str, username: str, content: str) -> dict[str, Any]:
    msg_id = uuid4().hex[:8]
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO chat_messages (id, user_id, username, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (msg_id, user_id, username, content, now),
        )
        conn.commit()
    return {
        "id": msg_id,
        "user_id": user_id,
        "username": username,
        "content": content,
        "created_at": now,
    }


def list_recent_messages(limit: int = 50) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, user_id, username, content, created_at
            FROM chat_messages
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [_row_to_dict(row) for row in reversed(rows)]
