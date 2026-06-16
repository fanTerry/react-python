import pytest
from starlette.websockets import WebSocketDisconnect

from chat_db import dm_room_id


def _register_and_token(client, username: str):
    client.post(
        "/api/auth/register",
        json={"username": username, "password": "123456"},
    )
    res = client.post(
        "/api/auth/login",
        json={"username": username, "password": "123456"},
    )
    data = res.json()["data"]
    return data["access_token"], data["user"]["id"]


def _skip_non_message(ws, expected_content=None):
    while True:
        msg = ws.receive_json()
        if msg.get("type") != "message":
            continue
        if expected_content is None or msg.get("content") == expected_content:
            return msg


def test_list_messages_requires_auth(client):
    res = client.get("/api/chat/messages")
    assert res.status_code == 401


def test_list_messages_empty(client, auth_headers):
    res = client.get("/api/chat/messages", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["room_id"] == "public"
    assert data["items"] == []


def test_list_rooms(client, auth_headers):
    res = client.get("/api/chat/rooms", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["public_room"] == "public"
    assert data["online_count"] == 0
    assert data["dm_rooms"] == []


def test_websocket_requires_valid_token(client):
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/api/chat/ws?token=invalid"):
            pass
    assert exc.value.code == 1008


def test_websocket_send_and_persist(client, auth_headers):
    token = auth_headers["Authorization"].split(" ", 1)[1]

    with client.websocket_connect(f"/api/chat/ws?token={token}") as ws:
        ws.send_json({"content": "你好，聊天室！"})
        msg = _skip_non_message(ws, "你好，聊天室！")
        assert msg["room_id"] == "public"
        assert msg["username"] == "tester"

    res = client.get("/api/chat/messages?room_id=public", headers=auth_headers)
    items = res.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["content"] == "你好，聊天室！"


def test_presence_on_connect(client, auth_headers):
    token = auth_headers["Authorization"].split(" ", 1)[1]

    with client.websocket_connect(f"/api/chat/ws?token={token}") as ws:
        joined = ws.receive_json()
        assert joined["type"] == "joined"
        assert joined["online_count"] == 1

        res = client.get("/api/chat/rooms", headers=auth_headers)
        assert res.json()["data"]["online_count"] == 1


def test_dm_message_isolated(client):
    token_a, id_a = _register_and_token(client, "alice")
    token_b, id_b = _register_and_token(client, "bob")
    token_c, _ = _register_and_token(client, "carol")

    room = dm_room_id(id_a, id_b)
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_c = {"Authorization": f"Bearer {token_c}"}

    with client.websocket_connect(f"/api/chat/ws?token={token_a}") as ws_a:
        ws_a.send_json({"type": "join", "room_id": room})
        assert ws_a.receive_json()["type"] == "joined"

        with client.websocket_connect(f"/api/chat/ws?token={token_b}") as ws_b:
            ws_b.send_json({"type": "join", "room_id": room})
            assert ws_b.receive_json()["type"] == "joined"

            ws_a.send_json({"content": "私密消息"})
            msg_b = _skip_non_message(ws_b, "私密消息")
            assert msg_b["room_id"] == room

    res = client.get(f"/api/chat/messages?room_id={room}", headers=headers_c)
    assert res.status_code == 403

    res = client.get(f"/api/chat/messages?room_id={room}", headers=headers_a)
    assert res.status_code == 200
    assert len(res.json()["data"]["items"]) == 1

    rooms = client.get("/api/chat/rooms", headers=headers_a).json()["data"]["dm_rooms"]
    assert len(rooms) == 1
    assert rooms[0]["room_id"] == room


def test_mention_notification(client):
    token_a, id_a = _register_and_token(client, "dana")
    token_b, _ = _register_and_token(client, "eric")

    with client.websocket_connect(f"/api/chat/ws?token={token_b}") as ws_b:
        ws_b.receive_json()  # joined

        with client.websocket_connect(f"/api/chat/ws?token={token_a}") as ws_a:
            ws_a.receive_json()  # joined
            ws_a.send_json({"content": "你好 @eric 看一下"})
            mention = ws_b.receive_json()
            while mention.get("type") != "mention":
                mention = ws_b.receive_json()
            assert mention["from_user"]["username"] == "dana"
            assert "eric" in mention["message"]["content"]

    res = client.get(
        "/api/chat/mentions/unread",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res.json()["data"]["count"] == 1


def test_dm_read_receipt(client):
    token_a, id_a = _register_and_token(client, "frank")
    token_b, id_b = _register_and_token(client, "grace")
    room = dm_room_id(id_a, id_b)

    with client.websocket_connect(f"/api/chat/ws?token={token_a}") as ws_a:
        ws_a.send_json({"type": "join", "room_id": room})
        ws_a.receive_json()

        with client.websocket_connect(f"/api/chat/ws?token={token_b}") as ws_b:
            ws_b.send_json({"type": "join", "room_id": room})
            ws_b.receive_json()

            ws_a.send_json({"content": "收到请回复"})
            msg = _skip_non_message(ws_a)
            msg_id = msg["id"]

            ws_b.send_json({"type": "read", "room_id": room})
            read_event = ws_a.receive_json()
            while read_event.get("type") != "read":
                read_event = ws_a.receive_json()
            assert read_event["user_id"] == id_b

    res = client.get(
        f"/api/chat/messages?room_id={room}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    items = res.json()["data"]["items"]
    assert items[0]["read"] is True
