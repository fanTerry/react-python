# 博客全栈项目

React + FastAPI 博客：Markdown 写作、分类/标签、JWT 登录、WebSocket 聊天、pytest、Docker。

## 技术栈

| 层       | 技术                                        |
| -------- | ------------------------------------------- |
| 前端     | React 19 + TypeScript + Vite + React Router |
| 后端     | Python + FastAPI + JWT + bcrypt + pytest    |
| 数据存储 | SQLite（`backend/todos.db`，历史文件名）    |

## 快速开始

### 后端

```bash
cd backend
python3 -m pip install -r requirements.txt
python3 -m uvicorn app:app --reload --port 8999
```

### 前端

```bash
cd frontend
bun install
bun run dev
```

- 前端：http://localhost:5173
- API 文档：http://localhost:8999/docs

### 测试

```bash
cd backend
python3 -m pytest -v
```

当前 **17 个测试**（博客 7 + 认证 4 + 个人中心 2 + 聊天 4）

### CI（GitHub Actions）

推送到 `master` / `main` 或开 PR 时自动运行：

- **Backend**：安装依赖 → `pytest -v`
- **Frontend**：`bun install` → `bun run build`（TypeScript + Vite 构建）

工作流文件：`.github/workflows/ci.yml`

在 GitHub 仓库的 **Actions** 标签页可查看每次运行结果；PR 上会显示检查是否通过。

### Docker

```bash
cp .env.example .env
docker compose up --build -d
```

访问 http://localhost:8080

## 功能

- Markdown 文章发布 / 编辑 / 删除
- 分类、标签、搜索、分页
- 注册 / 登录（JWT），仅作者可改自己的文章
- **WebSocket 公共聊天室**（登录后 `/chat`，消息持久化）
- 统一 API 响应 `{ code, message, data }`

## 项目结构

```
├── backend/
│   ├── app.py          # 应用入口
│   ├── auth_api.py     # 认证路由
│   ├── auth_db.py      # 用户数据
│   ├── blog_api.py     # 博客路由
│   ├── blog_db.py      # 文章 / 分类 / 标签
│   ├── chat_api.py     # WebSocket + 聊天 REST
│   ├── chat_db.py      # 聊天消息
│   ├── database.py     # SQLite 连接
│   └── tests/
├── frontend/src/
│   ├── api/            # client、auth、posts、chat
│   ├── context/        # AuthContext
│   ├── components/     # Layout、ProtectedRoute
│   └── pages/          # 博客、聊天、登录、注册
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## API 摘要

### 认证

| 方法 | 路径               | 说明     |
| ---- | ------------------ | -------- |
| POST | /api/auth/register | 注册     |
| POST | /api/auth/login    | 登录     |
| GET  | /api/auth/me       | 当前用户 |
| GET  | /api/auth/profile  | 个人中心（用户 + 我的文章） |

### 博客

| 方法   | 路径                       | 说明           |
| ------ | -------------------------- | -------------- |
| GET    | /api/posts                 | 列表           |
| GET    | /api/posts/meta/categories | 分类列表       |
| GET    | /api/posts/meta/tags       | 标签列表       |
| GET    | /api/posts/{id}            | 详情           |
| POST   | /api/posts                 | 发布（需登录） |
| PATCH  | /api/posts/{id}            | 更新（作者）   |
| DELETE | /api/posts/{id}            | 删除（作者）   |

### 聊天

| 方法      | 路径              | 说明                         |
| --------- | ----------------- | ---------------------------- |
| GET       | /api/chat/messages | 最近消息（需登录）           |
| WebSocket | /api/chat/ws?token= | 实时收发（query 传 JWT）     |

## 学习路线

见 [ROADMAP.md](./ROADMAP.md)
