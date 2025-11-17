#!/bin/bash

# 停止任务调度服务脚本
# 包含 FastAPI 服务和 Celery 任务队列的停止

set -e

echo "🛑 停止任务调度服务..."

# 停止容器内的 Celery 服务
echo "停止 Celery 服务..."
if docker ps | grep -q centurion-task-scheduler-service; then
    docker exec centurion-task-scheduler-service pkill -f "celery.*worker" 2>/dev/null || true
    docker exec centurion-task-scheduler-service pkill -f "celery.*beat" 2>/dev/null || true
    docker exec centurion-task-scheduler-service pkill -f "celery.*flower" 2>/dev/null || true
    echo "Celery 服务已停止"
else
    echo "任务调度服务容器未运行"
fi

# 停止任务调度服务容器
echo "停止任务调度服务容器..."
docker compose stop task-scheduler-service 2>/dev/null || true

# 检查本地进程（如果有的话）
echo "检查本地进程..."
PIDS=$(ps aux | grep -E "(uvicorn.*task-scheduler|python.*main\.py|celery)" | grep -v grep | awk '{print $2}' || true)

if [ -n "$PIDS" ]; then
    echo "发现运行中的本地进程，正在停止..."
    for PID in $PIDS; do
        echo "停止进程 $PID"
        kill -TERM $PID 2>/dev/null || true
    done
    
    # 等待进程优雅退出
    sleep 3
    
    # 检查是否还有进程运行
    REMAINING_PIDS=$(ps aux | grep -E "(uvicorn.*task-scheduler|python.*main\.py|celery)" | grep -v grep | awk '{print $2}' || true)
    if [ -n "$REMAINING_PIDS" ]; then
        echo "强制停止剩余进程..."
        for PID in $REMAINING_PIDS; do
            kill -KILL $PID 2>/dev/null || true
        done
    fi
    
    echo "本地进程已停止"
else
    echo "未发现运行中的本地进程"
fi

echo "✅ 任务调度服务已停止"