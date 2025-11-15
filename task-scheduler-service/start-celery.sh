#!/bin/bash
# Celery 启动脚本

echo "启动 Celery 服务..."

# 启动 Celery Worker
echo "启动 Celery Worker..."
celery -A celery_app worker --loglevel=info --queues=sync_queue,analysis_queue,default --detach

# 启动 Celery Beat
echo "启动 Celery Beat..."
celery -A celery_app beat --loglevel=info --detach

# 启动 Flower 监控界面
echo "启动 Flower 监控界面..."
celery -A celery_app flower --port=5555 --broker=redis://localhost:6379/0 --detach

echo "Celery 服务启动完成！"
echo "Flower 监控界面: http://localhost:5555"
echo "FastAPI 任务管理 API: http://localhost:8004/docs"