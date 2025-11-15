#!/bin/bash

# 定时任务服务启动脚本

echo "正在启动定时任务服务..."

# 检查是否安装了Docker
if ! command -v docker &> /dev/null; then
    echo "错误: 请先安装Docker"
    exit 1
fi

# 检查是否安装了Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "错误: 请先安装Docker Compose"
    exit 1
fi

# 构建并启动服务
echo "构建Docker镜像..."
docker-compose build

echo "启动服务..."
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo "检查服务状态..."
docker-compose ps

# 显示服务日志
echo "服务日志:"
docker-compose logs task-scheduler-service

echo ""
echo "定时任务服务已启动!"
echo "API文档地址: http://localhost:8004/docs"
echo "健康检查: http://localhost:8004/health"
echo ""
echo "使用以下命令查看日志:"
echo "docker-compose logs -f task-scheduler-service"
echo ""
echo "使用以下命令停止服务:"
echo "docker-compose down"