#!/bin/bash

# 基础设施服务启动脚本

set -e

echo "🚀 启动基础设施服务..."

# 启动PostgreSQL
echo "启动 PostgreSQL..."
docker compose up -d postgres

# 启动Redis
echo "启动 Redis..."
docker compose up -d redis

# 启动MinIO
echo "启动 MinIO..."
docker compose up -d minio

echo "等待服务就绪..."
sleep 10

echo "✅ 基础设施服务启动完成"
echo ""
echo "服务信息:"
echo "PostgreSQL: localhost:5432 (postgres/centurion123)"
echo "Redis:      localhost:6379 (密码: centurion123)"
echo "MinIO:      http://localhost:9001 (minioadmin/minioadmin123)"