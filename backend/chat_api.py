from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

import auth_db
import chat_db as db
from chat_db import PUBLIC_ROOM, can_access_room, dm_room_id
from deps import decode_token, get_current_user
from response import ApiResponse, ok

router = APIRouter(prefix="/api/chat", tags=["chat"])


@dataclass
class ConnectionState:
    websocket: WebSocket
    user: dict[str, Any]
    room_id: str = PUBLIC_ROOM


class ConnectionManager:
    def __init__(self) -> None:
        self.connections: dict[WebSocket, ConnectionState] = {}

    async def connect(self, websocket: WebSocket, user: dict[str, Any]) -> None:
        await websocket.accept()
        self.connections[websocket] = ConnectionState(websocket=websocket, user=user)

    def disconnect(self, websocket: WebSocket) -> None:
        self.connections.pop(websocket, None)

    def get_state(self, websocket: WebSocket) -> Optional[ConnectionState]:
        return self.connections.get(websocket)

    def set_room(self, websocket: WebSocket, room_id: str) -> None:
        state = self.connections.get(websocket)
        if state:
            state.room_id = room_id

    def online_users(self) -> list[dict[str, str]]:
        seen: dict[str, dict[str, str]] = {}
        for state in self.connections.values():
            seen[state.user["id"]] = {
                "id": state.user["id"],
                "username": state.user["username"],
            }
        return sorted(seen.values(), key=lambda u: u["username"])

    def online_count(self) -> int:
        return len(self.online_users())

    def connections_for_user(self, user_id: str) -> list[WebSocket]:
        return [
            websocket
            for websocket, state in self.connections.items()
            if state.user["id"] == user_id
        ]

    async def send_json(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        try:
            await websocket.send_json(message)
        except RuntimeError:
            self.disconnect(websocket)

    async def send_to_user(self, user_id: str, message: dict[str, Any]) -> None:
        for websocket in self.connections_for_user(user_id):
            await self.send_json(websocket, message)

    async def broadcast_all(self, message: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for websocket in list(self.connections):
            try:
                await websocket.send_json(message)
            except RuntimeError:
                dead.append(websocket)
        for websocket in dead:
            self.disconnect(websocket)

    async def broadcast_presence(self) -> None:
        await self.broadcast_all(
            {
                "type": "presence",
                "online_count": self.online_count(),
                "users": self.online_users(),
            }
        )

    async def broadcast_to_room(self, room_id: str, message: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for websocket, state in list(self.connections.items()):
            if state.room_id != room_id:
                continue
            try:
                await websocket.send_json(message)
            except RuntimeError:
                dead.append(websocket)
        for websocket in dead:
            self.disconnect(websocket)


manager = ConnectionManager()


class MarkMentionsReadBody(BaseModel):
    message_ids: Optional[list[str]] = None


async def _notify_mentions(
    message: dict[str, Any],
    sender: dict[str, Any],
    mentioned_users: list[dict[str, str]],
) -> None:
    payload = {
        "type": "mention",
        "message": message,
        "from_user": {"id": sender["id"], "username": sender["username"]},
    }
    for mention in mentioned_users:
        await manager.send_to_user(mention["id"], payload)


@router.get("/messages", response_model=ApiResponse)
def list_messages(
    room_id: str = Query(PUBLIC_ROOM),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    if not can_access_room(current_user["id"], room_id):
        raise HTTPException(status_code=403, detail="无权访问该房间")
    items = db.list_recent_messages(room_id, limit, viewer_id=current_user["id"])
    return ok({"room_id": room_id, "items": items})


@router.get("/rooms", response_model=ApiResponse)
def list_rooms(current_user: dict = Depends(get_current_user)):
    dm_rooms = db.list_dm_rooms(current_user["id"])
    return ok(
        {
            "public_room": PUBLIC_ROOM,
            "dm_rooms": dm_rooms,
            "online_count": manager.online_count(),
            "online_users": manager.online_users(),
            "unread_mentions": db.count_unread_mentions(current_user["id"]),
        }
    )


@router.get("/mentions/unread", response_model=ApiResponse)
def unread_mentions(
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    items = db.list_unread_mentions(current_user["id"], limit)
    return ok(
        {
            "count": db.count_unread_mentions(current_user["id"]),
            "items": items,
        }
    )


@router.post("/mentions/read", response_model=ApiResponse)
def mark_mentions_read(
    body: MarkMentionsReadBody,
    current_user: dict = Depends(get_current_user),
):
    count = db.mark_mentions_read(current_user["id"], body.message_ids)
    return ok({"marked": count})


@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket, token: str = Query(...)):
    user_id = decode_token(token)
    if user_id is None:
        await websocket.close(code=1008, reason="token 无效")
        return

    user = auth_db.get_user_by_id(user_id)
    if user is None:
        await websocket.close(code=1008, reason="用户不存在")
        return

    await manager.connect(websocket, user)
    await manager.send_json(
        websocket,
        {
            "type": "joined",
            "room_id": PUBLIC_ROOM,
            "online_count": manager.online_count(),
            "users": manager.online_users(),
            "unread_mentions": db.count_unread_mentions(user["id"]),
        },
    )
    await manager.broadcast_presence()

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "message")

            if msg_type == "join":
                room_id = str(data.get("room_id", PUBLIC_ROOM))
                if room_id.startswith("dm:") and room_id.count(":") == 2:
                    parts = room_id.split(":")
                    peer_id = parts[2] if parts[1] == user["id"] else parts[1]
                    if peer_id == user["id"]:
                        await manager.send_json(
                            websocket,
                            {"type": "error", "message": "不能与自己私聊"},
                        )
                        continue
                    if auth_db.get_user_by_id(peer_id) is None:
                        await manager.send_json(
                            websocket,
                            {"type": "error", "message": "对方用户不存在"},
                        )
                        continue
                    room_id = dm_room_id(user["id"], peer_id)

                if not can_access_room(user["id"], room_id):
                    await manager.send_json(
                        websocket, {"type": "error", "message": "无权进入该房间"}
                    )
                    continue

                manager.set_room(websocket, room_id)
                last_read_at = db.mark_room_read(user["id"], room_id)
                await manager.send_json(
                    websocket,
                    {"type": "joined", "room_id": room_id},
                )
                await manager.broadcast_to_room(
                    room_id,
                    {
                        "type": "read",
                        "room_id": room_id,
                        "user_id": user["id"],
                        "username": user["username"],
                        "last_read_at": last_read_at,
                    },
                )
                continue

            if msg_type == "read":
                state = manager.get_state(websocket)
                if state is None:
                    break
                room_id = str(data.get("room_id", state.room_id))
                if not can_access_room(user["id"], room_id):
                    continue
                last_read_at = db.mark_room_read(
                    user["id"],
                    room_id,
                    data.get("last_read_at"),
                )
                await manager.broadcast_to_room(
                    room_id,
                    {
                        "type": "read",
                        "room_id": room_id,
                        "user_id": user["id"],
                        "username": user["username"],
                        "last_read_at": last_read_at,
                    },
                )
                continue

            content = str(data.get("content", "")).strip()
            if not content:
                continue
            if len(content) > 2000:
                await manager.send_json(
                    websocket,
                    {"type": "error", "message": "消息过长（最多 2000 字）"},
                )
                continue

            state = manager.get_state(websocket)
            if state is None:
                break
            room_id = state.room_id
            if not can_access_room(user["id"], room_id):
                await manager.send_json(
                    websocket, {"type": "error", "message": "无权在该房间发言"}
                )
                continue

            message = db.create_message(user["id"], user["username"], content, room_id)
            mentioned_users = message.pop("mentioned_users", [])
            await manager.broadcast_to_room(
                room_id, {"type": "message", **message}
            )
            if mentioned_users:
                await _notify_mentions(message, user, mentioned_users)

            db.mark_room_read(user["id"], room_id, message["created_at"])
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)
        await manager.broadcast_presence()
