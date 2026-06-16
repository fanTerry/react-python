"""数据库连接：默认 SQLite；设置 DATABASE_URL 时使用 PostgreSQL。"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
DB_PATH = Path(os.environ.get("APP_DB_PATH", Path(__file__).parent / "todos.db"))


def is_postgres() -> bool:
    return bool(DATABASE_URL)


def _adapt_sql(sql: str) -> str:
    if is_postgres():
        return sql.replace("?", "%s")
    return sql


def excluded(column: str) -> str:
    """UPSERT 冲突行引用（SQLite / PostgreSQL 兼容）。"""
    return f"EXCLUDED.{column}" if is_postgres() else f"excluded.{column}"


class DBConnection:
    """统一 SQLite / PostgreSQL 的 execute / commit 接口。"""

    def __init__(self, conn: Any, postgres: bool) -> None:
        self._conn = conn
        self._postgres = postgres

    def execute(self, sql: str, params: tuple | list = ()):
        return self._conn.execute(_adapt_sql(sql), params)

    def commit(self) -> None:
        self._conn.commit()

    def rollback(self) -> None:
        self._conn.rollback()


@contextmanager
def get_connection() -> Iterator[DBConnection]:
    if is_postgres():
        import psycopg
        from psycopg.rows import dict_row

        raw = psycopg.connect(DATABASE_URL, row_factory=dict_row)
        wrapper = DBConnection(raw, True)
        try:
            yield wrapper
        except Exception:
            raw.rollback()
            raise
        finally:
            raw.close()
    else:
        raw = sqlite3.connect(DB_PATH)
        raw.row_factory = sqlite3.Row
        wrapper = DBConnection(raw, False)
        try:
            yield wrapper
        finally:
            raw.close()


def column_exists(conn: DBConnection, table: str, column: str) -> bool:
    if is_postgres():
        row = conn.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = ? AND column_name = ?
            """,
            (table, column),
        ).fetchone()
        return row is not None

    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in rows)


def ensure_column(conn: DBConnection, table: str, column: str, definition: str) -> None:
    if not column_exists(conn, table, column):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def row_value(row: Any, key: str, index: int = 0) -> Any:
    """兼容 sqlite3.Row 与 psycopg dict_row。"""
    if row is None:
        return None
    if isinstance(row, dict):
        return row.get(key, row.get(list(row.keys())[index] if row else None))
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return row[index]
