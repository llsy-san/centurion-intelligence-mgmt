#!/bin/bash

# 停止AI智能代理服务脚本

set -e

echo "=========================================="
echo "停止AI智能代理服务"
echo "=========================================="

echo "检查Docker服务状态..."
if command -v docker-compose &> /dev/null; then
    if docker-compose ps | grep -q "ai-agent-service"; then
        echo "停止AI智能代理服务Docker服务..."
        docker-compose stop ai-agent-service
        docker-compose rm -f ai-agent-service
        echo "Docker服务已停止"
    else
        echo "AI智能代理服务Docker服务未运行"
    fi
else
    echo "Docker Compose 未安装，跳过Docker服务检查"
fi

echo ""
echo "检查进程..."
PIDS=$(ps aux | grep -E "(uvicorn.*ai-agent-service|python.*ai-agent-service)" | grep -v grep | awk '{print $2}' || true)

if [ -n "$PIDS" ]; then
    echo "发现运行中的AI智能代理服务进程，正在停止..."
    for PID in $PIDS; do
        echo "停止进程 $PID"
        kill -TERM $PID 2>/dev/null || true
    done
    
    # 等待进程优雅退出
    sleep 3
    
    # 检查是否还有进程运行
    REMAINING_PIDS=$(ps aux | grep -E "(uvicorn.*ai-agent-service|python.*ai-agent-service)" | grep -v grep | awk '{print $2}' || true)
    if [ -n "$REMAINING_PIDS" ]; then
        echo "强制停止剩余进程..."
        for PID in $REMAINING_PIDS; do
            kill -KILL $PID 2>/dev/null || true
        done
    fi
    
    echo "AI智能代理服务进程已停止"
else
    echo "未发现运行中的AI智能代理服务进程"
fi

echo ""
echo "=========================================="
echo "AI智能代理服务停止完成!"
echo "=========================================="