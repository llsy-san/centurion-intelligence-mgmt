#!/bin/bash

# 百夫长智能管理系统完整启动脚本

echo "🚀 启动百夫长智能管理系统所有服务..."

# 检查环境变量文件
if [ ! -f .env ]; then
    echo "📝 创建环境变量文件..."
    cp .env.example .env
    echo "✅ 已创建 .env 文件"
fi

# 构建并启动所有服务
echo "🔨 构建 Docker 镜像..."
docker compose build

echo "🚀 启动所有服务..."
docker compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 检查服务状态
echo "🔍 检查服务状态..."
docker compose ps

echo ""
echo "✅ 所有服务启动完成！"
echo ""
echo "🌐 服务访问地址："
echo "  - API网关: http://localhost:8000"
echo "  - 订单服务: http://localhost:8001"
echo "  - 支付服务: http://localhost:8002"
echo "  - 发货服务: http://localhost:8003"
echo ""
echo "📚 API文档："
echo "  - API网关文档: http://localhost:8000/docs"
echo "  - 订单服务文档: http://localhost:8001/docs"
echo "  - 支付服务文档: http://localhost:8002/docs"
echo "  - 发货服务文档: http://localhost:8003/docs"
echo ""
echo "🔧 管理界面："
echo "  - RabbitMQ管理: http://localhost:15672 (guest/guest)"
echo ""
echo "📊 查看日志: docker compose logs -f"
echo "🛑 停止服务: docker compose down"