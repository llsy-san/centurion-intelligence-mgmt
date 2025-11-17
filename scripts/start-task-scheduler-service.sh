#!/bin/bash

# 任务调度服务启动脚本
# 集成了 FastAPI 服务和 Celery 任务队列

set -e

echo "🚀 启动任务调度服务..."

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

# 启动任务调度服务 Docker 容器
echo "启动任务调度服务容器..."
docker compose up -d task-scheduler-service
sleep 3

# 在容器内启动 Celery 服务
echo "启动 Celery Worker..."
docker exec centurion-task-scheduler-service celery -A app.celery.celery_app worker --loglevel=info --queues=sync_queue,analysis_queue,default --detach

echo "启动 Celery Beat..."
docker exec centurion-task-scheduler-service celery -A app.celery.celery_app beat --loglevel=info --detach

echo "启动 Flower 监控界面..."
docker exec centurion-task-scheduler-service celery -A app.celery.celery_app flower --port=5555 --broker=redis://:centurion123@redis:6379/0 --detach

echo "✅ 任务调度服务启动完成"
echo "📋 服务信息:"
echo "  - FastAPI API: http://localhost:8006"
echo "  - Flower 监控: http://localhost:5555"
echo "  - Celery Worker: 已启动"
echo "  - Celery Beat: 已启动"