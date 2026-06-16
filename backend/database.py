"""SQLite 数据库连接（博客与认证共用同一文件）。"""

import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.environ.get("APP_DB_PATH", Path(__file__).parent / "todos.db"))


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
