#!/bin/bash

# AI智能体服务启动脚本

set -e

echo "🚀 启动AI智能体服务..."

# 检查依赖服务
echo "检查依赖服务..."
if ! docker ps | grep -q centurion-postgres; then
    echo "启动 PostgreSQL..."
    docker compose up -d postgres
    sleep 5
fi

if ! docker ps | grep -q centurion-redis; then
    echo "启动 Redis..."
    docker compose up -d redis
    sleep 3
fi

# 启动AI智能体服务
echo "启动AI智能体服务..."
docker compose up -d ai-agent-service

echo "✅ AI智能体服务启动完成"
echo "访问地址: http://localhost:8005"