# 全栈 Todo 应用

React + FastAPI 全栈示例项目。

## 技术栈

| 层       | 技术                        |
| -------- | --------------------------- |
| 前端     | React 19 + TypeScript + Vite |
| 后端     | Python + FastAPI             |
| 数据存储 | 内存字典（演示用）           |

## 快速开始

### 1. 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload
```

后端默认运行在 http://localhost:8000，API 文档在 http://localhost:8000/docs。

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在 http://localhost:5173。

## 项目结构

```
├── backend/
│   ├── app.py              # FastAPI 应用入口
│   └── requirements.txt    # Python 依赖
├── frontend/
│   ├── src/
│   │   ├── App.tsx         # 主组件
│   │   ├── App.css         # 组件样式
│   │   ├── main.tsx        # 入口文件
│   │   └── index.css       # 全局样式
│   ├── package.json
│   └── vite.config.ts
├── ROADMAP.md              # Vue → React + Python 全栈学习路线（本地备份）
└── README.md
```

## 学习路线

从 Vue 转向 React + Python 全栈的阶段性计划与资源见 [ROADMAP.md](./ROADMAP.md)。

## API 接口

| 方法     | 路径               | 说明     |
| -------- | ------------------ | -------- |
| GET      | /api/todos         | 获取全部 |
| POST     | /api/todos         | 新增     |
| PATCH    | /api/todos/{id}    | 更新     |
| DELETE   | /api/todos/{id}    | 删除     |
