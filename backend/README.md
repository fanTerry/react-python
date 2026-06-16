# 博客 API 后端

基于 FastAPI 的全栈 API：Markdown 博客、JWT 认证、WebSocket 实时聊天。

## 启动

```bash
python3 -m pip install -r requirements.txt
python3 -m uvicorn app:app --reload --port 8999
```

- 服务：http://localhost:8999
- 文档：http://localhost:8999/docs

## 结构

```
backend/
├── app.py          # 应用入口
├── auth_api.py     # /api/auth
├── auth_db.py      # 用户表
├── blog_api.py     # /api/posts
├── blog_db.py      # 文章 / 分类 / 标签
├── chat_api.py     # WebSocket + 聊天 REST
├── chat_db.py      # 聊天消息 / 已读 / @提醒
├── database.py     # SQLite / PostgreSQL 双模式连接
├── response.py     # 统一响应格式
└── tests/
```

## 数据库

| 模式 | 触发条件 | 说明 |
|------|----------|------|
| SQLite（默认） | 不设置 `DATABASE_URL` | 文件 `backend/todos.db`，可用 `APP_DB_PATH` 覆盖 |
| PostgreSQL | 设置 `DATABASE_URL` | Docker Compose 自动注入；本地示例见根目录 README |

本地连 Docker 里的 Postgres（可选，需先 `docker compose up -d postgres` 并映射 5432 端口）：

```bash
export DATABASE_URL=postgresql://blog:blog@localhost:5432/blog
python3 -m uvicorn app:app --reload --port 8999
```

## 测试

```bash
python3 -m pytest -v
```
