#!/bin/bash

# 百夫长智能管理系统 - 快速启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 百夫长智能管理系统 - 快速启动${NC}"
echo "=================================================="

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker 未安装，请先安装 Docker${NC}"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo -e "${RED}❌ Docker 服务未启动，请启动 Docker${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Docker 环境检查通过${NC}"
}

# 检查端口占用
check_ports() {
    local ports=(5432 6379 8001 8002 8003 8004 8005 8006 9000 9001)
    local occupied_ports=()
    
    for port in "${ports[@]}"; do
        if lsof -i :$port &> /dev/null; then
            occupied_ports+=($port)
        fi
    done
    
    if [ ${#occupied_ports[@]} -gt 0 ]; then
        echo -e "${YELLOW}⚠️  以下端口被占用: ${occupied_ports[*]}${NC}"
        echo -e "${YELLOW}请停止相关服务或修改端口配置${NC}"
        read -p "是否继续启动？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo -e "${GREEN}✅ 端口检查通过${NC}"
    fi
}

# 创建环境配置
create_env() {
    if [ ! -f .env ]; then
        echo -e "${YELLOW}📝 创建环境配置文件...${NC}"
        cp .env.example .env
        echo -e "${GREEN}✅ 环境配置文件已创建${NC}"
        echo -e "${YELLOW}💡 请根据需要修改 .env 文件中的配置${NC}"
    else
        echo -e "${GREEN}✅ 环境配置文件已存在${NC}"
    fi
}

# 启动服务
start_services() {
    echo -e "${YELLOW}🐳 启动 Docker 服务...${NC}"
    
    # 构建并启动所有服务
    docker compose up -d --build
    
    echo -e "${GREEN}✅ 服务启动完成${NC}"
}

# 等待服务就绪
wait_for_services() {
    echo -e "${YELLOW}⏳ 等待服务就绪...${NC}"
    
    # 等待数据库就绪
    echo -n "等待 PostgreSQL..."
    while ! docker exec centurion-postgres pg_isready -U postgres &> /dev/null; do
        echo -n "."
        sleep 2
    done
    echo -e " ${GREEN}✅${NC}"
    
    # 等待Redis就绪
    echo -n "等待 Redis..."
    while ! docker exec centurion-redis redis-cli --no-auth-warning -a centurion123 ping &> /dev/null; do
        echo -n "."
        sleep 2
    done
    echo -e " ${GREEN}✅${NC}"
    
    # 等待API网关就绪
    echo -n "等待 API网关..."
    for i in {1..30}; do
        if curl -s http://localhost:8001/health &> /dev/null; then
            echo -e " ${GREEN}✅${NC}"
            break
        fi
        echo -n "."
        sleep 2
        if [ $i -eq 30 ]; then
            echo -e " ${YELLOW}⚠️${NC}"
        fi
    done
}

# 显示服务状态
show_status() {
    echo ""
    echo -e "${BLUE}📊 服务状态${NC}"
    echo "=================================================="
    docker compose ps
    
    echo ""
    echo -e "${BLUE}🌐 服务访问地址${NC}"
    echo "=================================================="
    echo -e "API网关:      ${GREEN}http://localhost:8001${NC}"
    echo -e "订单服务:     ${GREEN}http://localhost:8002${NC}"
    echo -e "支付服务:     ${GREEN}http://localhost:8003${NC}"
    echo -e "物流服务:     ${GREEN}http://localhost:8004${NC}"
    echo -e "AI智能体:     ${GREEN}http://localhost:8005${NC}"
    echo -e "任务调度:     ${GREEN}http://localhost:8006${NC}"
    echo -e "文件管理:     ${GREEN}http://localhost:9001${NC}"
    echo ""
    echo -e "API文档:      ${GREEN}http://localhost:8001/docs${NC}"
    echo -e "PostgreSQL:   ${GREEN}localhost:5432${NC} (postgres/centurion123)"
    echo -e "Redis:        ${GREEN}localhost:6379${NC} (密码: centurion123)"
    echo ""
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示帮助信息"
    echo "  --stop         停止所有服务"
    echo "  --restart      重启所有服务"
    echo "  --logs         查看服务日志"
    echo "  --status       查看服务状态"
    echo ""
    echo "示例:"
    echo "  $0             # 启动所有服务"
    echo "  $0 --stop      # 停止所有服务"
    echo "  $0 --restart   # 重启所有服务"
    echo "  $0 --logs      # 查看日志"
}

# 停止服务
stop_services() {
    echo -e "${YELLOW}⏹️  停止所有服务...${NC}"
    docker compose down
    echo -e "${GREEN}✅ 服务已停止${NC}"
}

# 重启服务
restart_services() {
    echo -e "${YELLOW}🔄 重启所有服务...${NC}"
    docker compose restart
    echo -e "${GREEN}✅ 服务已重启${NC}"
}

# 查看日志
show_logs() {
    echo -e "${BLUE}📋 服务日志${NC}"
    docker compose logs -f
}

# 查看状态
show_service_status() {
    echo -e "${BLUE}📊 服务状态${NC}"
    docker compose ps
}

# 主函数
main() {
    case "${1:-}" in
        -h|--help)
            show_help
            exit 0
            ;;
        --stop)
            stop_services
            exit 0
            ;;
        --restart)
            restart_services
            exit 0
            ;;
        --logs)
            show_logs
            exit 0
            ;;
        --status)
            show_service_status
            exit 0
            ;;
        "")
            # 默认启动流程
            check_docker
            check_ports
            create_env
            start_services
            wait_for_services
            show_status
            
            echo -e "${GREEN}🎉 百夫长智能管理系统启动完成！${NC}"
            echo -e "${BLUE}💡 使用 '$0 --help' 查看更多选项${NC}"
            ;;
        *)
            echo -e "${RED}❌ 未知选项: $1${NC}"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"