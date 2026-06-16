import pytest
from starlette.websockets import WebSocketDisconnect


def test_list_messages_requires_auth(client):
    res = client.get("/api/chat/messages")
    assert res.status_code == 401


def test_list_messages_empty(client, auth_headers):
    res = client.get("/api/chat/messages", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["items"] == []


def test_websocket_requires_valid_token(client):
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/api/chat/ws?token=invalid"):
            pass
    assert exc.value.code == 1008


def test_websocket_send_and_persist(client, auth_headers):
    token = auth_headers["Authorization"].split(" ", 1)[1]

    with client.websocket_connect(f"/api/chat/ws?token={token}") as ws:
        ws.send_json({"content": "你好，聊天室！"})
        msg = ws.receive_json()
        assert msg["type"] == "message"
        assert msg["content"] == "你好，聊天室！"
        assert msg["username"] == "tester"
        assert "id" in msg
        assert "created_at" in msg

    res = client.get("/api/chat/messages", headers=auth_headers)
    items = res.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["content"] == "你好，聊天室！"
