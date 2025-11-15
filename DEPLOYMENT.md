# 部署指南

## 快速开始

### 1. 使用脚本启动（推荐）

```bash
# 启动开发环境（仅基础服务）
./scripts/start-dev.sh

# 启动所有服务
./scripts/start-all.sh

# 停止所有服务
./scripts/stop-all.sh
```

### 2. 手动启动

#### 开发环境
```bash
# 1. 复制环境变量文件
cp .env.example .env

# 2. 安装Python依赖
pip install -r requirements.txt

# 3. 启动基础服务
make dev

# 4. 分别启动各个服务
cd order-service/app && python main.py &
cd payment-service/app && python main.py &
cd shipping-service/app && python main.py &
cd api-gateway/app && python main.py &
```

#### 生产环境
```bash
# 使用Docker Compose启动
make up

# 或者
cd docker-compose
docker-compose up -d
```

## 环境变量配置

复制 `.env.example` 为 `.env` 并修改以下关键配置：

```bash
# 数据库配置
DB_HOST=localhost
DB_PASSWORD=your_secure_password

# JWT密钥（生产环境必须修改）
JWT_SECRET_KEY=your-very-secure-secret-key

# 支付配置
ALIPAY_APP_ID=your_alipay_app_id
WECHAT_APP_ID=your_wechat_app_id
```

## 服务健康检查

```bash
# 检查所有服务状态
curl http://localhost:8000/health  # API网关
curl http://localhost:8001/health  # 订单服务
curl http://localhost:8002/health  # 支付服务
curl http://localhost:8003/health  # 发货服务
```

## 监控和日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f order-service
docker-compose logs -f payment-service
```

## 数据库初始化

服务启动时会自动创建数据库表。如需手动初始化：

```bash
# 进入任一服务容器
docker exec -it order-service bash

# 运行数据库初始化
python -c "from database import init_db; import asyncio; asyncio.run(init_db())"
```

## 性能优化

### 1. 数据库优化
- 配置连接池大小
- 添加适当的索引
- 定期清理日志

### 2. 缓存策略
- Redis缓存热点数据
- 设置合适的过期时间

### 3. 负载均衡
- 使用Nginx作为反向代理
- 配置多个服务实例

## 安全配置

### 1. JWT密钥
生产环境必须使用强密钥：
```bash
# 生成安全的JWT密钥
openssl rand -hex 32
```

### 2. 数据库安全
- 使用强密码
- 限制数据库访问IP
- 定期备份数据

### 3. 网络安全
- 使用HTTPS
- 配置防火墙
- 限制服务间通信

## 故障排除

### 常见问题

1. **服务无法启动**
   - 检查端口是否被占用
   - 查看服务日志
   - 验证环境变量配置

2. **数据库连接失败**
   - 检查数据库服务状态
   - 验证连接参数
   - 检查网络连通性

3. **服务间调用失败**
   - 检查服务发现配置
   - 验证网络连通性
   - 查看API网关日志

### 日志级别

开发环境：
```bash
DEBUG=true
```

生产环境：
```bash
DEBUG=false
```

## 扩展部署

### 水平扩展
```yaml
# docker-compose.yml
order-service:
  deploy:
    replicas: 3
```

### 使用Kubernetes
参考 `k8s/` 目录下的配置文件（需要单独创建）。

## 备份和恢复

### 数据库备份
```bash
# 备份
docker exec postgres pg_dump -U postgres order_system > backup.sql

# 恢复
docker exec -i postgres psql -U postgres order_system < backup.sql
```

### Redis备份
```bash
# 备份
docker exec redis redis-cli BGSAVE