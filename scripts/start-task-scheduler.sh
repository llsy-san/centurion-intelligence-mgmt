#!/bin/bash

# 启动定时任务服务脚本

set -e

echo "=========================================="
echo "启动定时任务服务"
echo "=========================================="

# 检查当前目录
if [ ! -f "task-scheduler-service/app/main.py" ]; then
    echo "错误: 请在项目根目录下运行此脚本"
    exit 1
fi

# 进入服务目录
cd task-scheduler-service

echo "1. 检查依赖..."
if [ ! -f "requirements.txt" ]; then
    echo "错误: requirements.txt 文件不存在"
    exit 1
fi

echo "2. 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 请先安装Python 3"
    exit 1
fi

echo "3. 运行功能测试..."
if [ -f "test_service.py" ]; then
    echo "执行服务测试..."
    python3 test_service.py
    echo "测试完成!"
else
    echo "跳过测试 (test_service.py 不存在)"
fi

echo ""
echo "4. 启动选项:"
echo "   [1] Docker 方式启动 (推荐)"
echo "   [2] 直接启动 (需要手动安装依赖)"
echo "   [3] 仅运行测试"
echo ""

read -p "请选择启动方式 (1-3): " choice

case $choice in
    1)
        echo "使用Docker启动服务..."
        if ! command -v docker &> /dev/null; then
            echo "错误: 请先安装Docker"
            exit 1
        fi
        
        if ! command -v docker-compose &> /dev/null; then
            echo "错误: 请先安装Docker Compose"
            exit 1
        fi
        
        echo "构建Docker镜像..."
        docker-compose build
        
        echo "启动服务..."
        docker-compose up -d
        
        echo "等待服务启动..."
        sleep 10
        
        echo "检查服务状态..."
        docker-compose ps
        
        echo ""
        echo "=========================================="
        echo "定时任务服务启动完成!"
        echo "=========================================="
        echo "API文档: http://localhost:8004/docs"
        echo "健康检查: http://localhost:8004/health"
        echo ""
        echo "查看日志: docker-compose logs -f task-scheduler-service"
        echo "停止服务: docker-compose down"
        echo "=========================================="
        ;;
        
    2)
        echo "直接启动服务..."
        echo "注意: 请确保已安装所有依赖和数据库服务"
        
        # 检查虚拟环境
        if [ -z "$VIRTUAL_ENV" ]; then
            echo "建议使用虚拟环境运行服务"
            echo "创建虚拟环境: python3 -m venv venv"
            echo "激活虚拟环境: source venv/bin/activate"
        fi
        
        echo "安装依赖..."
        pip3 install -r requirements.txt
        
        echo "启动服务..."
        python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload
        ;;
        
    3)
        echo "仅运行测试..."
        python3 test_service.py
        echo "测试完成!"
        ;;
        
    *)
        echo "无效选择"
        exit 1
        ;;
esac