#!/bin/bash

# 停止所有服务脚本

set -e

echo "=========================================="
echo "停止百夫长智能管理系统所有服务"
echo "=========================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🛑 停止所有微服务..."

# 停止各个服务
echo ""
echo "停止任务调度服务..."
bash "$SCRIPT_DIR/stop-task-scheduler.sh"

echo ""
echo "停止AI智能代理服务..."
bash "$SCRIPT_DIR/stop-ai-service.sh"

echo ""
echo "停止物流服务..."
bash "$SCRIPT_DIR/stop-shipping-service.sh"

echo ""
echo "停止支付服务..."
bash "$SCRIPT_DIR/stop-payment-service.sh"

echo ""
echo "停止订单服务..."
bash "$SCRIPT_DIR/stop-order-service.sh"

echo ""
echo "停止API网关..."
bash "$SCRIPT_DIR/stop-api-gateway.sh"

echo ""
echo "🛑 停止基础设施服务..."
if command -v docker-compose &> /dev/null; then
    echo "停止所有Docker服务..."
    docker-compose down
    
    echo "清理未使用的容器..."
    docker container prune -f
    
    echo "清理未使用的网络..."
    docker network prune -f
else
    echo "Docker Compose 未安装，跳过Docker清理"
fi

echo ""
echo "=========================================="
echo "✅ 所有服务停止完成!"
echo "=========================================="