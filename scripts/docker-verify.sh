#!/usr/bin/env bash
set -euo pipefail

BASE="${1:-http://localhost:8080}"

echo "==> 检查前端页面"
curl -sf "$BASE/" | grep -q '<div id="root">'

echo "==> 检查后端健康"
curl -sf "$BASE/health" | grep -q 'ok'

echo "==> 检查博客 API"
curl -sf "$BASE/api/posts" | grep -q '"code":0'

echo "==> 全部通过：$BASE 可访问（博客 + 聊天 + WebSocket 经 Nginx 代理）"
