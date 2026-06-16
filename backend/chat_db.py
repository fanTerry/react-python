"""聊天消息 SQLite 数据层（公共大厅 + 私聊房间 + 已读 + @提醒）。"""

import re
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

import auth_db
from database import ensure_column, excluded, get_connection, is_postgres

PUBLIC_ROOM = "public"
MENTION_PATTERN = re.compile(r"@(\w{3,32})")


def dm_room_id(user_id_a: str, user_id_b: str) -> str:
    a, b = sorted([user_id_a, user_id_b])
    return f"dm:{a}:{b}"


def dm_peer_id(room_id: str, user_id: str) -> Optional[str]:
    if not room_id.startswith("dm:"):
        return None
    parts = room_id.split(":")
    if len(parts) != 3:
        return None
    return parts[2] if parts[1] == user_id else parts[1]


def can_access_room(user_id: str, room_id: str) -> bool:
    if room_id == PUBLIC_ROOM:
        return True
    if room_id.startswith("dm:"):
        parts = room_id.split(":")
        if len(parts) != 3:
            return False
        return user_id in (parts[1], parts[2])
    return False


def init_chat_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                username TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                room_id TEXT NOT NULL DEFAULT 'public'
            )
            """
        )
        if not is_postgres():
            ensure_column(conn, "chat_messages", "room_id", "TEXT DEFAULT 'public'")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_room_reads (
                user_id TEXT NOT NULL,
                room_id TEXT NOT NULL,
                last_read_at TEXT NOT NULL,
                PRIMARY KEY (user_id, room_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS message_mentions (
                message_id TEXT NOT NULL,
                mentioned_user_id TEXT NOT NULL,
                mentioned_username TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (message_id, mentioned_user_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS mention_reads (
                user_id TEXT NOT NULL,
                message_id TEXT NOT NULL,
                read_at TEXT NOT NULL,
                PRIMARY KEY (user_id, message_id)
            )
            """
        )
        conn.execute(
            "UPDATE chat_messages SET room_id = ? WHERE room_id IS NULL",
            (PUBLIC_ROOM,),
        )
        conn.commit()


def _row_to_dict(row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "room_id": row["room_id"] or PUBLIC_ROOM,
        "user_id": row["user_id"],
        "username": row["username"],
        "content": row["content"],
        "created_at": row["created_at"],
    }


def parse_mention_usernames(content: str) -> list[str]:
    seen: set[str] = set()
    names: list[str] = []
    for match in MENTION_PATTERN.findall(content):
        key = match.lower()
        if key in seen:
            continue
        seen.add(key)
        names.append(match)
    return names


def resolve_mentions(content: str, sender_id: str) -> list[dict[str, str]]:
    resolved: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for username in parse_mention_usernames(content):
        user = auth_db.get_user_by_username(username)
        if user is None or user["id"] == sender_id or user["id"] in seen_ids:
            continue
        seen_ids.add(user["id"])
        resolved.append({"id": user["id"], "username": user["username"]})
    return resolved


def _store_mentions(
    conn,
    message_id: str,
    mentions: list[dict[str, str]],
    created_at: str,
) -> None:
    for mention in mentions:
        conn.execute(
            """
            INSERT INTO message_mentions
            (message_id, mentioned_user_id, mentioned_username, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (message_id, mentioned_user_id) DO NOTHING
            """,
            (message_id, mention["id"], mention["username"], created_at),
        )


def _mentions_for_message_ids(message_ids: list[str]) -> dict[str, list[str]]:
    if not message_ids:
        return {}
    placeholders = ",".join("?" * len(message_ids))
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT message_id, mentioned_username
            FROM message_mentions
            WHERE message_id IN ({placeholders})
            ORDER BY mentioned_username
            """,
            message_ids,
        ).fetchall()
    result: dict[str, list[str]] = {}
    for row in rows:
        result.setdefault(row["message_id"], []).append(row["mentioned_username"])
    return result


def get_room_read_at(user_id: str, room_id: str) -> Optional[str]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT last_read_at FROM chat_room_reads
            WHERE user_id = ? AND room_id = ?
            """,
            (user_id, room_id),
        ).fetchone()
    return row["last_read_at"] if row else None


def mark_room_read(user_id: str, room_id: str, last_read_at: Optional[str] = None) -> str:
    if last_read_at is None:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT created_at FROM chat_messages
                WHERE room_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (room_id,),
            ).fetchone()
        last_read_at = row["created_at"] if row else datetime.now(timezone.utc).isoformat()

    existing = get_room_read_at(user_id, room_id)
    if existing and existing >= last_read_at:
        return existing

    with get_connection() as conn:
        conn.execute(
            f"""
            INSERT INTO chat_room_reads (user_id, room_id, last_read_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, room_id) DO UPDATE SET
                last_read_at = {excluded("last_read_at")}
            """,
            (user_id, room_id, last_read_at),
        )
        conn.commit()
    return last_read_at


def _enrich_messages(items: list[dict[str, Any]], viewer_id: str, room_id: str) -> None:
    mention_map = _mentions_for_message_ids([m["id"] for m in items])
    peer_id = dm_peer_id(room_id, viewer_id)
    peer_read_at = get_room_read_at(peer_id, room_id) if peer_id else None

    for msg in items:
        msg["mentions"] = mention_map.get(msg["id"], [])
        if room_id.startswith("dm:") and msg["user_id"] == viewer_id:
            msg["read"] = bool(peer_read_at and msg["created_at"] <= peer_read_at)
        else:
            msg["read"] = None


def create_message(
    user_id: str,
    username: str,
    content: str,
    room_id: str = PUBLIC_ROOM,
) -> dict[str, Any]:
    msg_id = uuid4().hex[:8]
    now = datetime.now(timezone.utc).isoformat()
    mentions = resolve_mentions(content, user_id)

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO chat_messages (id, user_id, username, content, created_at, room_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (msg_id, user_id, username, content, now, room_id),
        )
        _store_mentions(conn, msg_id, mentions, now)
        conn.commit()

    message = {
        "id": msg_id,
        "room_id": room_id,
        "user_id": user_id,
        "username": username,
        "content": content,
        "created_at": now,
        "mentions": [m["username"] for m in mentions],
        "mentioned_users": mentions,
        "read": None,
    }
    return message


def list_recent_messages(
    room_id: str = PUBLIC_ROOM,
    limit: int = 50,
    viewer_id: Optional[str] = None,
) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, room_id, user_id, username, content, created_at
            FROM chat_messages
            WHERE room_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (room_id, limit),
        ).fetchall()
    items = [_row_to_dict(row) for row in reversed(rows)]
    if viewer_id:
        _enrich_messages(items, viewer_id, room_id)
    return items


def list_dm_rooms(user_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT room_id
            FROM chat_messages
            WHERE room_id LIKE 'dm:%'
              AND (room_id LIKE ? OR room_id LIKE ?)
            ORDER BY room_id
            """,
            (f"dm:{user_id}:%", f"dm:%:{user_id}"),
        ).fetchall()

        rooms: list[dict[str, Any]] = []
        for row in rows:
            room_id = row["room_id"]
            parts = room_id.split(":")
            if len(parts) != 3:
                continue
            peer_id = parts[2] if parts[1] == user_id else parts[1]
            peer = conn.execute(
                "SELECT id, username FROM users WHERE id = ?",
                (peer_id,),
            ).fetchone()
            if peer is None:
                continue
            rooms.append(
                {
                    "room_id": room_id,
                    "peer": {"id": peer["id"], "username": peer["username"]},
                }
            )
    return rooms


def list_unread_mentions(user_id: str, limit: int = 20) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                mm.message_id,
                mm.mentioned_username,
                mm.created_at AS mention_at,
                m.room_id,
                m.user_id AS from_user_id,
                m.username AS from_username,
                m.content
            FROM message_mentions mm
            JOIN chat_messages m ON m.id = mm.message_id
            LEFT JOIN mention_reads mr
                ON mr.message_id = mm.message_id AND mr.user_id = ?
            WHERE mm.mentioned_user_id = ? AND mr.message_id IS NULL
            ORDER BY mm.created_at DESC
            LIMIT ?
            """,
            (user_id, user_id, limit),
        ).fetchall()

    return [
        {
            "message_id": row["message_id"],
            "room_id": row["room_id"],
            "from_user": {
                "id": row["from_user_id"],
                "username": row["from_username"],
            },
            "content": row["content"],
            "created_at": row["mention_at"],
        }
        for row in rows
    ]


def count_unread_mentions(user_id: str) -> int:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM message_mentions mm
            LEFT JOIN mention_reads mr
                ON mr.message_id = mm.message_id AND mr.user_id = ?
            WHERE mm.mentioned_user_id = ? AND mr.message_id IS NULL
            """,
            (user_id, user_id),
        ).fetchone()
    return int(row["cnt"])


def mark_mentions_read(user_id: str, message_ids: Optional[list[str]] = None) -> int:
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        if message_ids:
            count = 0
            for message_id in message_ids:
                cur = conn.execute(
                    """
                    INSERT INTO mention_reads (user_id, message_id, read_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT (user_id, message_id) DO NOTHING
                    """,
                    (user_id, message_id, now),
                )
                count += cur.rowcount
        else:
            rows = conn.execute(
                """
                SELECT mm.message_id
                FROM message_mentions mm
                LEFT JOIN mention_reads mr
                    ON mr.message_id = mm.message_id AND mr.user_id = ?
                WHERE mm.mentioned_user_id = ? AND mr.message_id IS NULL
                """,
                (user_id, user_id),
            ).fetchall()
            count = 0
            for row in rows:
                cur = conn.execute(
                    """
                    INSERT INTO mention_reads (user_id, message_id, read_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT (user_id, message_id) DO NOTHING
                    """,
                    (user_id, row["message_id"], now),
                )
                count += cur.rowcount
        conn.commit()
    return count
