import { useEffect, useState } from "react";
import "./App.css";

const API = "http://localhost:8000/api/todos";

interface Todo {
  id: string;
  title: string;
  completed: boolean;
  created_at: string;
}

function App() {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");

  const fetchTodos = async () => {
    const res = await fetch(API);
    setTodos(await res.json());
    setLoading(false);
  };

  useEffect(() => {
    let active = true;
    fetch(API)
      .then((res) => res.json())
      .then((data) => {
        if (active) {
          setTodos(data);
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const addTodo = async () => {
    const title = input.trim();
    if (!title) return;
    await fetch(API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    });
    setInput("");
    fetchTodos();
  };

  const toggleTodo = async (todo: Todo) => {
    await fetch(`${API}/${todo.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ completed: !todo.completed }),
    });
    fetchTodos();
  };

  const deleteTodo = async (id: string) => {
    await fetch(`${API}/${id}`, { method: "DELETE" });
    fetchTodos();
  };

  const startEdit = (todo: Todo) => {
    setEditingId(todo.id);
    setEditText(todo.title);
  };

  const saveEdit = async (id: string) => {
    const title = editText.trim();
    if (!title) return;
    await fetch(`${API}/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    });
    setEditingId(null);
    fetchTodos();
  };

  const remaining = todos.filter((t) => !t.completed).length;

  return (
    <div className="app">
      <header className="header">
        <h1>Todo App</h1>
        <p className="subtitle">React + FastAPI 全栈示例</p>
      </header>

      <div className="input-bar">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addTodo()}
          placeholder="添加新任务..."
          autoFocus
        />
        <button className="btn-add" onClick={addTodo}>
          添加
        </button>
      </div>

      {loading ? (
        <p className="status">加载中...</p>
      ) : todos.length === 0 ? (
        <p className="status empty">暂无任务，添加一个吧！</p>
      ) : (
        <>
          <ul className="todo-list">
            {todos.map((todo) => (
              <li key={todo.id} className={todo.completed ? "done" : ""}>
                <input
                  type="checkbox"
                  checked={todo.completed}
                  onChange={() => toggleTodo(todo)}
                />

                {editingId === todo.id ? (
                  <input
                    className="edit-input"
                    value={editText}
                    onChange={(e) => setEditText(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && saveEdit(todo.id)}
                    onBlur={() => saveEdit(todo.id)}
                    autoFocus
                  />
                ) : (
                  <span
                    className="title"
                    onDoubleClick={() => startEdit(todo)}
                  >
                    {todo.title}
                  </span>
                )}

                <div className="actions">
                  {editingId !== todo.id && (
                    <button
                      className="btn-edit"
                      onClick={() => startEdit(todo)}
                    >
                      编辑
                    </button>
                  )}
                  <button
                    className="btn-delete"
                    onClick={() => deleteTodo(todo.id)}
                  >
                    删除
                  </button>
                </div>
              </li>
            ))}
          </ul>
          <footer className="footer">
            还有 <strong>{remaining}</strong> 项未完成
          </footer>
        </>
      )}
    </div>
  );
}

export default App;
