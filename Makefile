# 百夫长智能管理系统 - Makefile

.PHONY: help start stop restart status logs clean build test

# 默认目标
help:
	@echo "百夫长智能管理系统 - 可用命令:"
	@echo ""
	@echo "  make start          - 启动所有服务"
	@echo "  make stop           - 停止所有服务"
	@echo "  make restart        - 重启所有服务"
	@echo "  make status         - 查看服务状态"
	@echo "  make logs           - 查看服务日志"
	@echo "  make clean          - 清理Docker资源"
	@echo "  make build          - 构建Docker镜像"
	@echo "  make test           - 运行测试"
	@echo ""
	@echo "单独服务命令:"
	@echo "  make start-infra    - 启动基础设施(数据库、Redis、MinIO)"
	@echo "  make start-api      - 启动API网关"
	@echo "  make start-order    - 启动订单服务"
	@echo "  make start-payment  - 启动支付服务"
	@echo "  make start-shipping - 启动物流服务"
	@echo "  make start-ai       - 启动AI智能体"
	@echo "  make start-task     - 启动任务调度"
	@echo "  make monitor-task       - 查看任务调度服务状态"
	@echo ""
	@echo "停止服务命令:"
	@echo "  make stop-api       - 停止API网关"
	@echo "  make stop-order     - 停止订单服务"
	@echo "  make stop-payment   - 停止支付服务"
	@echo "  make stop-shipping  - 停止物流服务"
	@echo "  make stop-ai        - 停止AI智能体"
	@echo "  make stop-task      - 停止任务调度"
	@echo "  make stop-all       - 停止所有服务"

# 启动所有服务
start:
	@echo "🚀 启动百夫长智能管理系统..."
	@./scripts/quick-start.sh

# 停止所有服务
stop:
	@echo "🛑 停止所有服务..."
	@docker compose down

# 重启所有服务
restart:
	@echo "🔄 重启所有服务..."
	@docker compose down
	@docker compose up -d --build

# 查看服务状态
status:
	@echo "📊 服务状态:"
	@docker compose ps

# 查看服务日志
logs:
	@echo "📋 查看服务日志:"
	@docker compose logs -f

# 清理Docker资源
clean:
	@echo "🧹 清理Docker资源..."
	@docker compose down -v
	@docker system prune -f
	@docker volume prune -f

# 构建Docker镜像
build:
	@echo "🔨 构建Docker镜像..."
	@docker compose build --no-cache

# 运行测试
test:
	@echo "🧪 运行测试..."
	@docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

# 启动基础设施
start-infra:
	@echo "🏗️ 启动基础设施..."
	@./scripts/start-infrastructure.sh

# 启动API网关
start-api:
	@echo "🌐 启动API网关..."
	@./scripts/start-api-gateway.sh

# 启动订单服务
start-order:
	@echo "📦 启动订单服务..."
	@./scripts/start-order-service.sh

# 启动支付服务
start-payment:
	@echo "💳 启动支付服务..."
	@./scripts/start-payment-service.sh

# 启动物流服务
start-shipping:
	@echo "🚚 启动物流服务..."
	@./scripts/start-shipping-service.sh

# 启动AI智能体
start-ai:
	@echo "🤖 启动AI智能体..."
	@./scripts/start-ai-service.sh

# 启动任务调度
start-task:
	@echo "⏰ 启动任务调度..."
	@./scripts/start-task-scheduler-service.sh

monitor-task:
	@echo "📊 任务调度服务监控:"
	@echo "=== Docker 容器状态 ==="
	@docker compose ps | grep task-scheduler
	@echo ""
	@echo "=== Celery 进程状态 ==="
	@docker exec centurion-task-scheduler-service ps aux | grep -E "(celery|uvicorn)" | grep -v grep || true
	@echo ""
	@echo "=== 端口占用 ==="
	@lsof -i :8006 -i :5555 || true

# 停止API网关
stop-api:
	@echo "🛑 停止API网关..."
	@./scripts/stop-api-gateway.sh

# 停止订单服务
stop-order:
	@echo "🛑 停止订单服务..."
	@./scripts/stop-order-service.sh

# 停止支付服务
stop-payment:
	@echo "🛑 停止支付服务..."
	@./scripts/stop-payment-service.sh

# 停止物流服务
stop-shipping:
	@echo "🛑 停止物流服务..."
	@./scripts/stop-shipping-service.sh

# 停止AI智能体
stop-ai:
	@echo "🛑 停止AI智能体..."
	@./scripts/stop-ai-service.sh

# 停止任务调度
stop-task:
	@echo "🛑 停止任务调度..."
	@./scripts/stop-task-scheduler.sh

# 停止所有服务
stop-all:
	@echo "🛑 停止所有服务..."
	@./scripts/stop-all.sh