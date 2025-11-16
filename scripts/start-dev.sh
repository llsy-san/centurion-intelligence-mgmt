#!/bin/bash

# 百夫长智能管理系统开发环境启动脚本

echo "🚀 启动百夫长智能管理系统开发环境..."

# 检查是否安装了必要的依赖
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 创建环境变量文件
if [ ! -f .env ]; then
    echo "📝 创建环境变量文件..."
    cp .env.example .env
    echo "✅ 已创建 .env 文件，请根据需要修改配置"
fi

# 启动基础服务
echo "🔧 启动基础服务 (PostgreSQL, Redis, RabbitMQ)..."
cd docker-compose
docker-compose up -d postgres redis rabbitmq

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose ps

echo ""
echo "✅ 基础服务启动完成！"
echo ""
echo "📊 服务访问地址："
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo "  - RabbitMQ: localhost:5672 (管理界面: http://localhost:15672)"
echo ""
echo "🔧 接下来可以启动应用服务："
echo "  1. 订单服务: cd ../order-service/app && python main.py"
echo "  2. 支付服务: cd ../payment-service/app && python main.py"
echo "  3. 发货服务: cd ../shipping-service/app && python main.py"
echo "  4. API网关: cd ../api-gateway/app && python main.py"
echo ""
echo "📚 或者使用 Docker 启动所有服务："
echo "  docker-compose up -d"
echo ""
echo "🌐 API文档地址："
echo "  - API网关: http://localhost:8000/docs"
echo "  - 订单服务: http://localhost:8001/docs"
echo "  - 支付服务: http://localhost:8002/docs"
echo "  - 发货服务: http://localhost:8003/docs"