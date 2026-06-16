import pytest
from fastapi.testclient import TestClient

import auth_db
import blog_db
import chat_db
import database


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """每个测试使用独立的临时数据库。"""
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    auth_db.init_users_db()
    blog_db.init_posts_db()
    chat_db.init_chat_db()

    from app import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def auth_headers(client):
    client.post(
        "/api/auth/register",
        json={"username": "tester", "password": "123456"},
    )
    res = client.post(
        "/api/auth/login",
        json={"username": "tester", "password": "123456"},
    )
    token = res.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
