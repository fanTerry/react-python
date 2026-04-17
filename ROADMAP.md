# Vue 前端 → React + Python 全栈工程师学习路线

基于 Vue 开发经验定制的学习路线，预计 **8–10 周**系统掌握（每天约 4–6 小时；全职可压缩到约 5–6 周）。

| 指标 | 说明 |
|------|------|
| 总学习周期 | 8–10 周 |
| 阶段数 | 4 |
| 实战项目建议 | 5 个（由易到难） |
| 起点 | Vue 经验迁移到 React |

---

## Vue vs React 概念对照

你已经掌握的 Vue 概念在 React 中都有对应，理解映射关系是最快的入门方式。

| Vue 概念 | React 对应 |
|----------|------------|
| 模板 `<template>` | JSX（函数返回值） |
| `ref()` / `reactive()` | `useState()` |
| `computed()` | `useMemo()` |
| `watch()` / `watchEffect()` | `useEffect()` |
| `onMounted()` 等生命周期 | `useEffect()` 统一处理 |
| Composables | Custom Hooks |
| `v-if` / `v-for` | 三元表达式 / `.map()` |
| `v-model` | `value` + `onChange` |
| `provide` / `inject` | Context API |
| Pinia | Zustand / Redux |
| Vue Router | React Router |
| Slots | `children` / render props |

---

## Phase 1 — React 核心（1–2 周）

**目标**：利用 Vue 经验快速迁移到 React 思维模型。

| 主题 | 说明 | 时间 | 优先级 |
|------|------|------|--------|
| JSX 语法 vs 模板语法 | Vue `<template>` → JSX 返回值 | 1 天 | 高 |
| 组件 & Props | 与 Vue props 几乎一致，重点学 children | 1 天 | 高 |
| useState / useReducer | 对应 Vue 的 `ref()` / `reactive()` | 2 天 | 高 |
| useEffect | 对应 `onMounted` + `watch`，心智模型不同 | 2 天 | 高 |
| 自定义 Hook | 类似 Vue Composables | 1 天 | 高 |
| React Router | 对应 Vue Router | 1 天 | 中 |
| 状态管理 (Zustand) | 比 Redux 轻量，类似 Pinia | 2 天 | 中 |
| TypeScript + React | 泛型组件、事件类型、Props 类型 | 2 天 | 高 |

---

## Phase 2 — Python 基础（2 周）

**目标**：掌握 Python 语言核心，为后端开发打基础。

| 主题 | 说明 | 时间 | 优先级 |
|------|------|------|--------|
| 基础语法 | 变量、类型、控制流、函数 | 2 天 | 高 |
| 数据结构 | list / dict / set / tuple | 1 天 | 高 |
| 面向对象 | class、继承、dataclass、dunder 方法 | 2 天 | 中 |
| 模块与包管理 | import、pip、venv | 1 天 | 高 |
| 类型注解 | type hints | 1 天 | 高 |
| 异步编程 | async/await | 2 天 | 高 |
| 常用标准库 | pathlib / json / datetime / collections | 1 天 | 中 |
| 错误处理 | try/except/finally | 1 天 | 中 |

---

## Phase 3 — FastAPI 后端（2 周）

**目标**：用 FastAPI 构建生产级 REST API。

| 主题 | 说明 | 时间 | 优先级 |
|------|------|------|--------|
| 路由与请求处理 | GET/POST/PUT/DELETE，路径与查询参数 | 1 天 | 高 |
| Pydantic 数据校验 | 请求/响应模型、自动文档 | 2 天 | 高 |
| 依赖注入 | Depends()、会话、认证 | 2 天 | 高 |
| 中间件 & CORS | 跨域、日志、异常 | 1 天 | 高 |
| 数据库 (SQLAlchemy) | ORM、Alembic、CRUD | 3 天 | 高 |
| 认证与授权 | JWT、OAuth2、bcrypt | 2 天 | 高 |
| 文件上传 & 静态文件 | UploadFile、静态资源 | 1 天 | 中 |
| 测试 (pytest) | TestClient、fixture | 2 天 | 中 |

---

## Phase 4 — 全栈整合（2 周）

**目标**：打通前后端，掌握全栈开发工作流。

| 主题 | 说明 | 时间 | 优先级 |
|------|------|------|--------|
| 前后端联调 | Axios/fetch、API 类型、错误处理 | 2 天 | 高 |
| Docker 容器化 | Dockerfile、docker-compose | 2 天 | 高 |
| 数据库选型 | PostgreSQL、Redis 入门 | 2 天 | 高 |
| 部署上线 | Nginx、HTTPS、云服务器基础 | 2 天 | 中 |
| CI/CD | GitHub Actions | 1 天 | 中 |
| 日志与监控 | logging、Sentry | 1 天 | 中 |
| 环境管理 | .env、多环境 (dev/staging/prod) | 1 天 | 中 |

---

## 实战项目路线（由易到难）

每完成一个阶段，立刻做对应难度的项目，边学边练效果最好。

| 项目 | 描述 | 核心技能 | 难度 |
|------|------|----------|------|
| Todo 全栈应用（本仓库） | 基础 CRUD + 前后端分离 | React、FastAPI、REST | 入门 |
| 博客系统 | 发布/编辑、Markdown、分页、搜索 | 数据库、富文本、分页 | 初级 |
| 用户认证平台 | 注册/登录、JWT、角色、个人中心 | JWT、bcrypt、路由守卫 | 中级 |
| 实时聊天应用 | WebSocket、在线状态、消息持久化 | WebSocket、消息队列 | 中级 |
| 电商后台管理系统 | 商品、订单、报表、上传 | 复杂表单、图表、事务 | 进阶 |

---

## 学习方法论

### 高效策略

1. **概念迁移优先**：用 Vue 经验理解 React，重点看差异点。
2. **项目驱动**：每个阶段配一个实战项目，遇到问题再查文档。
3. **前后端交替**：每天前端 + 后端各半，尽早体验全栈联调。

### 常见误区

1. **别陷入框架对比**：学 React 时用 React 的方式思考。
2. **别追求一次学完**：先掌握核心约 80%，其余在项目中补。
3. **别跳过 Python 基础**：直接写 FastAPI 容易在语言层卡住，花约 2 周打基础值得。

---

## 推荐学习资源

| 资源 | 地址 | 说明 |
|------|------|------|
| React 官方文档 | https://react.dev | 交互式教程，必读 |
| FastAPI 官方文档 | https://fastapi.tiangolo.com | 文档与示例质量高 |
| Python 官方教程 | https://docs.python.org/zh-cn/3/tutorial | 中文版系统入门 |
| Full Stack Python | https://www.fullstackpython.com | Python Web 全景 |
| freeCodeCamp | https://www.freecodecamp.org | 免费实战课程 |

---

## 下一步行动

从本仓库的 Todo 全栈项目开始：先读 React 官方教程的交互章节，再在本项目里加功能（筛选、排序、分页等），在实战中巩固基础。
