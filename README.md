# 博客全栈项目

React + FastAPI 博客：Markdown 写作、分类/标签、JWT 登录、WebSocket 聊天、pytest、Docker。

## 技术栈

| 层       | 技术                                        |
| -------- | ------------------------------------------- |
| 前端     | React 19 + TypeScript + Vite + React Router |
| 后端     | Python + FastAPI + JWT + bcrypt + pytest    |
| 数据存储 | SQLite（本地开发）/ PostgreSQL（Docker 生产） |

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

当前 **22 个测试**（博客 7 + 认证 4 + 个人中心 2 + 聊天 9）

### CI（GitHub Actions）

推送到 `master` / `main` 或开 PR 时自动运行：

- **Backend**：安装依赖 → `pytest -v`
- **Frontend**：`bun install` → `bun run build`（TypeScript + Vite 构建）

工作流文件：`.github/workflows/ci.yml`

在 GitHub 仓库的 **Actions** 标签页可查看每次运行结果；PR 上会显示检查是否通过。

### Docker（一键部署）

```bash
cp .env.example .env          # 首次部署：修改 JWT_SECRET
docker compose up --build -d  # 构建并后台启动
docker compose ps            # 确认 backend healthy、frontend running
bash scripts/docker-verify.sh
```

访问 **http://localhost:8080**（端口可在 `.env` 的 `FRONTEND_PORT` 修改）

| 容器 | 作用 |
|------|------|
| `fullstack-postgres` | PostgreSQL 16（数据卷 `pg-data`） |
| `fullstack-backend` | FastAPI，通过 `DATABASE_URL` 连接 Postgres |
| `fullstack-frontend` | Nginx 静态页 + 反向代理 `/api/`（含 WebSocket） |

**数据库策略：**

| 环境 | 配置 |
|------|------|
| 本地开发 | 不设置 `DATABASE_URL` → 自动用 `backend/todos.db`（SQLite） |
| Docker | 自动注入 `DATABASE_URL=postgresql://blog:blog@postgres:5432/blog` |
| pytest | 临时 SQLite 文件，无需 Postgres |

**常用命令：**

```bash
docker compose logs -f          # 查看日志
docker compose down             # 停止并删除容器（数据卷保留）
docker compose down -v          # 停止并清空数据库卷（慎用）
docker compose up --build -d    # 代码更新后重新构建
```

**验证清单：**

1. 打开 http://localhost:8080 → 注册 / 登录
2. 发布一篇博客文章
3. 进入 **聊天** → 双开浏览器测试私聊、@提醒

**数据持久化：** PostgreSQL 数据在 Docker 卷 `pg-data`；`docker compose down` 不丢数据，`docker compose down -v` 会清空。

**Docker Hub 拉镜像超时（国内常见）：**

Docker Desktop → Settings → Docker Engine，加入镜像加速后 Apply：

```json
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://docker.xuanyuan.me"
  ]
}
```

或使用阿里云/DaoCloud 等个人镜像地址。配置后执行 `docker compose pull` 再 `docker compose up --build -d`。

**架构：**

```
浏览器 :8080 → Nginx (frontend)
                 ├─ /          → React 静态文件
                 └─ /api/*     → backend:8999（REST + WebSocket）
                                    └─ PostgreSQL (pg-data)
```

## 功能

- Markdown 文章发布 / 编辑 / 删除
- 分类、标签、搜索、分页
- 注册 / 登录（JWT），仅作者可改自己的文章
- **WebSocket 公共聊天室**（登录后 `/chat`，消息持久化）
- **在线人数** + **私聊房间**（点击在线用户发起 DM，仅双方可见）
- **消息已读**（私聊中显示「已读/未读」）+ **@提醒**（实时通知 + 导航栏红点）
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
│   ├── database.py     # SQLite / PostgreSQL 双模式
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

| 方法      | 路径                | 说明                               |
| --------- | ------------------- | ---------------------------------- |
| GET       | /api/chat/messages  | 房间历史（`room_id=public` 或 `dm:a:b`） |
| GET       | /api/chat/rooms     | 在线人数 + 在线用户 + 历史私聊 + 未读@数 |
| GET       | /api/chat/mentions/unread | 未读 @ 提醒列表              |
| POST      | /api/chat/mentions/read   | 标记 @ 已读                  |
| WebSocket | /api/chat/ws?token= | 实时收发；`join` 切换房间          |

**WebSocket 协议：**

- 客户端 → 服务端：`{ "type": "join", "room_id": "public" \| "dm:..." }`
- 客户端 → 服务端：`{ "type": "read", "room_id": "..." }`（标记已读）
- 客户端 → 服务端：`{ "content": "消息 @username ..." }`（在当前房间发言，@ 会触发提醒）
- 服务端 → 客户端：`presence`（在线人数）、`joined`、`read`（已读回执）、`mention`（@提醒）、`message`

## 学习路线

见 [ROADMAP.md](./ROADMAP.md)
