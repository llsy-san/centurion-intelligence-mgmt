# Celery 任务管理平台 Makefile

.PHONY: help install test start-dev start-prod stop clean

help:
	@echo "Celery 任务管理平台命令:"
	@echo "  install     - 安装依赖"
	@echo "  test        - 测试 Celery 集成"
	@echo "  start-dev   - 启动开发环境"
	@echo "  start-prod  - 启动生产环境 (Docker)"
	@echo "  stop        - 停止所有服务"
	@echo "  clean       - 清理临时文件"
	@echo "  worker      - 启动 Celery Worker"
	@echo "  beat        - 启动 Celery Beat"
	@echo "  flower      - 启动 Flower 监控"
	@echo "  monitor     - 查看服务状态"

install:
	@echo "📦 安装依赖..."
	pip install -r requirements.txt

test:
	@echo "🧪 测试 Celery 集成..."
	python test_celery_integration.py

start-dev:
	@echo "🚀 启动开发环境..."
	@echo "启动 Redis..."
	redis-server --daemonize yes
	@echo "启动 Celery Worker..."
	celery -A celery_app worker --loglevel=info --detach
	@echo "启动 Celery Beat..."
	celery -A celery_app beat --loglevel=info --detach
	@echo "启动 Flower..."
	celery -A celery_app flower --port=5555 --detach
	@echo "启动 FastAPI..."
	uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload

start-prod:
	@echo "🐳 启动生产环境 (Docker)..."
	docker-compose up -d
	@echo "服务已启动:"
	@echo "  - FastAPI: http://localhost:8004"
	@echo "  - Flower:  http://localhost:5555"

stop:
	@echo "🛑 停止所有服务..."
	-docker-compose down
	-pkill -f "celery.*worker"
	-pkill -f "celery.*beat"
	-pkill -f "celery.*flower"
	-pkill -f "uvicorn.*main"
	@echo "所有服务已停止"

worker:
	@echo "👷 启动 Celery Worker..."
	celery -A celery_app worker --loglevel=info --queues=sync_queue,analysis_queue,default

beat:
	@echo "⏰ 启动 Celery Beat..."
	celery -A celery_app beat --loglevel=info

flower:
	@echo "🌸 启动 Flower 监控..."
	celery -A celery_app flower --port=5555 --broker=redis://localhost:6379/0

monitor:
	@echo "📊 服务状态监控:"
	@echo "=== Docker 容器状态 ==="
	-docker-compose ps
	@echo ""
	@echo "=== 进程状态 ==="
	-ps aux | grep -E "(celery|uvicorn|redis)" | grep -v grep
	@echo ""
	@echo "=== 端口占用 ==="
	-lsof -i :8004 -i :5555 -i :6379

clean:
	@echo "🧹 清理临时文件..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "celerybeat-schedule*" -delete
	@echo "清理完成"

# 快捷命令
dev: start-dev
prod: start-prod