from typing import Any

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

import auth_db
import chat_db as db
from deps import decode_token, get_current_user
from response import ApiResponse, ok

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except RuntimeError:
                dead.append(connection)
        for connection in dead:
            self.disconnect(connection)


manager = ConnectionManager()


@router.get("/messages", response_model=ApiResponse)
def list_messages(
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    items = db.list_recent_messages(limit)
    return ok({"items": items})


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

    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            content = str(data.get("content", "")).strip()
            if not content:
                continue
            if len(content) > 2000:
                await websocket.send_json(
                    {"type": "error", "message": "消息过长（最多 2000 字）"}
                )
                continue

            message = db.create_message(user["id"], user["username"], content)
            await manager.broadcast({"type": "message", **message})
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)
