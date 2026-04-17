from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from uuid import uuid4

app = FastAPI(title="Todo API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

todos: dict[str, dict] = {}


class TodoCreate(BaseModel):
    title: str


class TodoUpdate(BaseModel):
    title: str | None = None
    completed: bool | None = None


@app.get("/api/todos")
def list_todos():
    return sorted(todos.values(), key=lambda t: t["created_at"])


@app.post("/api/todos", status_code=201)
def create_todo(body: TodoCreate):
    from datetime import datetime, timezone

    todo_id = uuid4().hex[:8]
    todo = {
        "id": todo_id,
        "title": body.title,
        "completed": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    todos[todo_id] = todo
    return todo


@app.patch("/api/todos/{todo_id}")
def update_todo(todo_id: str, body: TodoUpdate):
    if todo_id not in todos:
        raise HTTPException(404, "Todo not found")
    if body.title is not None:
        todos[todo_id]["title"] = body.title
    if body.completed is not None:
        todos[todo_id]["completed"] = body.completed
    return todos[todo_id]


@app.delete("/api/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: str):
    if todo_id not in todos:
        raise HTTPException(404, "Todo not found")
    del todos[todo_id]
