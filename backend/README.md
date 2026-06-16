# 博客 API 后端

基于 FastAPI 的博客 REST API：Markdown 文章、分类/标签、JWT 认证。

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
├── database.py     # SQLite 连接
├── response.py     # 统一响应格式
└── tests/
```

## 数据库

- 文件：`backend/todos.db`（历史文件名，含用户与博客数据）
- 环境变量 `APP_DB_PATH` 可覆盖路径

## 测试

```bash
python3 -m pytest -v
```
