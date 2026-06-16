# 构建阶段：用 Bun 打包前端
FROM oven/bun:1 AS builder

WORKDIR /app

COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

COPY . .

# 空字符串 = 浏览器走同域 /api（由 nginx 转发）
ENV VITE_API_BASE_URL=
RUN bun run build

# 运行阶段：Nginx 托管静态文件
FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
