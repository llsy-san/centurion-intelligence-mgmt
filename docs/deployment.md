# 百夫长智能管理系统 - 部署指南

## 🚀 快速开始

### 一键启动（推荐）

```bash
# 快速启动所有服务
make start

# 或者直接运行脚本
./scripts/quick-start.sh
```

### 查看服务状态

```bash
# 查看服务状态
make status

# 查看服务日志
make logs
```

### 停止服务

```bash
# 停止所有服务
make stop

# 重启所有服务
make restart
```

## 📋 服务列表

| 服务 | 端口 | 描述 | 启动脚本 |
|------|------|------|----------|
| API网关 | 8001 | 统一API入口 | `make start-api` |
| 订单服务 | 8002 | 订单管理 | `make start-order` |
| 支付服务 | 8003 | 支付处理 | `make start-payment` |
| 物流服务 | 8004 | 物流管理 | `make start-shipping` |
| AI智能体 | 8005 | AI服务 | `make start-ai` |
| 任务调度 | 8006 | 定时任务 | `make start-task` |
| PostgreSQL | 5432 | 数据库 | `make start-infra` |
| Redis | 6379 | 缓存 | `make start-infra` |
| MinIO | 9000/9001 | 文件存储 | `make start-infra` |

## 🔧 环境要求

- Docker 20.0+
- Docker Compose 2.0+
- 8GB+ 内存
- 10GB+ 磁盘空间

## 📁 项目结构

```
centurion-intelligence-mgmt/
├── docker-compose.yml          # Docker编排配置
├── Makefile                    # 构建脚本
├── DEPLOYMENT.md              # 部署文档
├── scripts/                   # 启动脚本
│   ├── quick-start.sh         # 快速启动脚本
│   ├── start-infrastructure.sh # 基础设施启动
│   ├── start-api-gateway.sh   # API网关启动
│   ├── start-order-service.sh # 订单服务启动
│   ├── start-payment-service.sh # 支付服务启动
│   ├── start-shipping-service.sh # 物流服务启动
│   ├── start-ai-service.sh    # AI服务启动
│   └── start-task-scheduler.sh # 任务调度启动
├── api-gateway/               # API网关服务
├── order-service/             # 订单服务
├── payment-service/           # 支付服务
├── shipping-service/          # 物流服务
├── ai-agent-service/          # AI智能体服务
└── task-scheduler-service/    # 任务调度服务
```

## 🌐 访问地址

启动完成后，可以通过以下地址访问服务：

- **API网关**: http://localhost:8001
- **API文档**: http://localhost:8001/docs
- **文件管理**: http://localhost:9001 (minioadmin/minioadmin123)

## 🔧 配置说明

### 环境变量

系统会自动创建 `.env` 文件，包含以下配置：

```bash
# 数据库配置
DATABASE_URL=postgresql://postgres:centurion123@localhost:5432/centurion_db
POSTGRES_PASSWORD=centurion123

# Redis配置
REDIS_URL=redis://:centurion123@localhost:6379
REDIS_PASSWORD=centurion123

# 文件服务配置
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123

# AI服务配置
OPENAI_API_KEY=your-openai-api-key

# 调试模式
DEBUG=true
LOG_LEVEL=INFO
```

### 修改配置

如需修改配置，请编辑 `.env` 文件，然后重启服务：

```bash
vim .env
make restart
```

## 🛠️ 开发模式

### 单独启动服务

```bash
# 先启动基础设施
make start-infra

# 然后启动需要的业务服务
make start-api      # API网关
make start-order    # 订单服务
make start-payment  # 支付服务
```

### 查看特定服务日志

```bash
# 查看API网关日志
docker logs -f centurion-api-gateway

# 查看订单服务日志
docker logs -f centurion-order-service
```

## 🆘 故障排除

### 常见问题

1. **端口冲突**
   ```bash
   # 检查端口占用
   lsof -i :8001
   
   # 停止占用端口的进程或修改配置
   ```

2. **服务启动失败**
   ```bash
   # 查看服务日志
   docker logs centurion-api-gateway
   
   # 重启服务
   docker restart centurion-api-gateway
   ```

3. **数据库连接失败**
   ```bash
   # 检查数据库状态
   docker exec centurion-postgres pg_isready -U postgres
   
   # 重启数据库
   docker restart centurion-postgres
   ```

### 清理和重置

```bash
# 停止所有服务并清理数据
make clean

# 重新启动
make start
```

## 📞 技术支持

如遇到问题，请：

1. 查看服务日志：`make logs`
2. 检查服务状态：`make status`
3. 尝试重启服务：`make restart`
4. 清理并重新部署：`make clean && make start`

---

**注意**: 首次启动可能需要几分钟时间来下载Docker镜像和初始化数据库。