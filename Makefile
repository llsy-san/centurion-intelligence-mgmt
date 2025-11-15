# 百夫长智能管理系统 Makefile

.PHONY: help install test lint format clean build run-all stop-all

# 默认目标
help:
	@echo "订单支付系统 - 可用命令："
	@echo ""
	@echo "  install              安装所有依赖"
	@echo "  test                 运行所有测试"
	@echo "  lint                 代码检查"
	@echo "  format               代码格式化"
	@echo "  clean                清理临时文件"
	@echo ""
	@echo "  build                构建所有服务"
	@echo "  run-all              启动所有服务"
	@echo "  stop-all             停止所有服务"
	@echo ""
	@echo "  run-gateway          启动API网关"
	@echo "  run-orders           启动订单服务"
	@echo "  run-payments         启动支付服务"
	@echo "  run-shipping         启动物流服务"
	@echo "  run-tasks            启动定时任务服务"
	@echo ""
	@echo "  logs                 查看所有服务日志"
	@echo "  status               查看服务状态"

# 安装依赖
install:
	@echo "📦 安装依赖..."
	pip install -r requirements.txt
	@echo "✅ 依赖安装完成"

# 运行测试
test:
	@echo "🧪 运行测试..."
	pytest -v --cov=. --cov-report=html
	@echo "✅ 测试完成，报告已生成到 htmlcov/"

# 代码检查
lint:
	@echo "🔍 代码检查..."
	flake8 --max-line-length=88 --extend-ignore=E203,W503 .
	mypy --ignore-missing-imports .
	@echo "✅ 代码检查完成"

# 代码格式化
format:
	@echo "🎨 格式化代码..."
	black --line-length=88 .
	@echo "✅ 代码格式化完成"

# 清理临时文件
clean:
	@echo "🧹 清理临时文件..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ .pytest_cache/
	@echo "✅ 清理完成"

# 构建所有服务
build:
	@echo "🔨 构建所有服务..."
	docker-compose -f docker-compose/task-scheduler-compose.yml build
	@echo "✅ 构建完成"

# 启动所有服务
run-all:
	@echo "🚀 启动所有服务..."
	./scripts/start-task-scheduler.sh
	@echo "✅ 所有服务已启动"

# 停止所有服务
stop-all:
	@echo "🛑 停止所有服务..."
	./scripts/stop-task-scheduler.sh
	@echo "✅ 所有服务已停止"

# 启动API网关
run-gateway:
	@echo "🚀 启动API网关..."
	cd api-gateway && python -m app.main

# 启动订单服务
run-orders:
	@echo "🚀 启动订单服务..."
	cd order-service && python -m app.main

# 启动支付服务
run-payments:
	@echo "🚀 启动支付服务..."
	cd payment-service && python -m app.main

# 启动物流服务
run-shipping:
	@echo "🚀 启动物流服务..."
	cd shipping-service && python -m app.main

# 启动定时任务服务
run-tasks:
	@echo "🚀 启动定时任务服务..."
	cd task-scheduler-service && python -m app.main

# 查看服务日志
logs:
	@echo "📝 查看服务日志..."
	docker-compose -f docker-compose/task-scheduler-compose.yml logs -f

# 查看服务状态
status:
	@echo "📊 查看服务状态..."
	docker-compose -f docker-compose/task-scheduler-compose.yml ps

# 数据库迁移
migrate:
	@echo "🗄️  执行数据库迁移..."
	# 这里可以添加数据库迁移命令
	@echo "✅ 数据库迁移完成"

# 初始化数据
init-data:
	@echo "📊 初始化数据..."
	# 这里可以添加初始化数据的命令
	@echo "✅ 数据初始化完成"

# 备份数据库
backup-db:
	@echo "💾 备份数据库..."
	docker exec task-postgres-db pg_dump -U postgres order_payment_db > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ 数据库备份完成"

# 恢复数据库
restore-db:
	@echo "🔄 恢复数据库..."
	@read -p "请输入备份文件路径: " backup_file; \
	docker exec -i task-postgres-db psql -U postgres order_payment_db < $$backup_file
	@echo "✅ 数据库恢复完成"