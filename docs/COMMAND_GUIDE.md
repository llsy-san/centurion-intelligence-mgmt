# 命令操作文档

## 项目概述

本文档提供订单支付系统的完整命令操作指南，包括开发环境搭建、服务启动、测试、部署等各个环节的命令操作。

## 环境要求

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 6+
- Node.js 18+ (如需前端开发)

## 1. 项目初始化

### 克隆项目
```bash
# 克隆代码仓库
git clone <repository-url>
cd order-payment-system

# 查看项目结构
tree -L 2
```

### 环境配置
```bash
# 复制环境变量配置文件
cp .env.example .env

# 编辑环境变量（根据实际情况修改）
vim .env
```

### Python环境设置
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 验证安装
pip list
```

## 2. 数据库操作

### PostgreSQL数据库
```bash
# 启动PostgreSQL容器
docker run -d \
  --name postgres-order-system \
  -e POSTGRES_DB=order_system \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:15

# 连接数据库
psql -h localhost -U postgres -d order_system

# 查看数据库状态
docker exec -it postgres-order-system psql -U postgres -c "\l"
```

### 数据库迁移
```bash
# 初始化Alembic
cd order-service
alembic init alembic

# 生成迁移文件
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head

# 查看迁移历史
alembic history

# 回滚迁移
alembic downgrade -1
```

### Redis缓存
```bash
# 启动Redis容器
docker run -d \
  --name redis-order-system \
  -p 6379:6379 \
  redis:7-alpine

# 连接Redis
redis-cli -h localhost -p 6379

# 测试Redis连接
redis-cli ping
```

## 3. 服务启动

### 单个服务启动
```bash
# 启动订单服务
cd order-service
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# 启动支付服务
cd payment-service
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

# 启动发货服务
cd shipping-service
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload

# 启动API网关
cd api-gateway
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 启动AI Agent服务
cd ai-agent-service
uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload
```

### 使用Docker Compose启动所有服务
```bash
# 进入docker-compose目录
cd docker-compose

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f order-service

# 停止所有服务
docker-compose down

# 重启特定服务
docker-compose restart shipping-service
```

### 使用Makefile快速操作
```bash
# 查看可用命令
make help

# 启动开发环境
make dev

# 启动生产环境
make prod

# 运行测试
make test

# 代码格式化
make format

# 代码检查
make lint

# 构建Docker镜像
make build

# 清理环境
make clean
```

## 4. 开发调试

### 代码质量检查
```bash
# 代码格式化
black .
black --check .  # 检查而不修改

# 导入排序
isort .
isort --check-only .  # 检查而不修改

# 代码风格检查
flake8 .
flake8 --statistics .

# 类型检查
mypy .
mypy --strict .

# 安全检查
bandit -r .
safety check
```

### 测试命令
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_orders.py

# 运行特定测试函数
pytest tests/test_orders.py::test_create_order

# 生成测试覆盖率报告
pytest --cov=app tests/
pytest --cov=app --cov-report=html tests/

# 运行性能测试
pytest tests/performance/ -v

# 运行集成测试
pytest tests/integration/ -v
```

### 数据库操作命令
```bash
# 查看数据库连接
psql -h localhost -U postgres -d order_system -c "SELECT version();"

# 备份数据库
pg_dump -h localhost -U postgres order_system > backup.sql

# 恢复数据库
psql -h localhost -U postgres order_system < backup.sql

# 查看表结构
psql -h localhost -U postgres -d order_system -c "\dt"

# 查看表数据
psql -h localhost -U postgres -d order_system -c "SELECT * FROM orders LIMIT 10;"

# 清空测试数据
psql -h localhost -U postgres -d order_system -c "TRUNCATE TABLE orders CASCADE;"
```

## 5. API测试

### 使用curl测试API
```bash
# 健康检查
curl -X GET http://localhost:8000/health

# 创建订单
curl -X POST http://localhost:8000/api/v1/orders/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "items": [
      {
        "product_id": "ticket_001",
        "product_name": "黄山风景区门票",
        "product_type": "ticket",
        "quantity": 2,
        "unit_price": 190.0,
        "total_price": 380.0,
        "scenic_area_id": "huangshan_001",
        "scenic_area_name": "黄山风景区",
        "valid_days": 30,
        "ticket_type": "成人票"
      }
    ],
    "shipping_address": "安徽省黄山市",
    "phone": "13800138000"
  }'

# 查询订单
curl -X GET http://localhost:8000/api/v1/orders/ORD20241030001

# 支付订单
curl -X POST http://localhost:8000/api/v1/payments/ \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ORD20241030001",
    "amount": 380.0,
    "payment_method": "alipay"
  }'

# 查询用户资产
curl -X GET http://localhost:8000/api/v1/shipping/assets/user/user_001

# 使用门票
curl -X POST http://localhost:8000/api/v1/shipping/assets/TICKET_20241030001/use
```

### 使用httpie测试API
```bash
# 安装httpie
pip install httpie

# 创建订单
http POST localhost:8000/api/v1/orders/ \
  user_id=user_001 \
  items:='[{
    "product_id": "ticket_001",
    "product_name": "黄山风景区门票",
    "product_type": "ticket",
    "quantity": 1,
    "unit_price": 190.0,
    "total_price": 190.0,
    "scenic_area_id": "huangshan_001",
    "scenic_area_name": "黄山风景区",
    "valid_days": 30,
    "ticket_type": "成人票"
  }]' \
  shipping_address="安徽省黄山市" \
  phone="13800138000"

# 查询订单
http GET localhost:8000/api/v1/orders/ORD20241030001
```

## 6. 监控和日志

### 查看服务日志
```bash
# 查看Docker容器日志
docker logs -f order-service
docker logs -f shipping-service
docker logs -f payment-service

# 查看应用日志文件
tail -f logs/order-service.log
tail -f logs/shipping-service.log

# 实时监控日志
tail -f logs/*.log | grep ERROR
```

### 性能监控
```bash
# 查看系统资源使用
htop
docker stats

# 查看数据库连接
psql -h localhost -U postgres -d order_system -c "SELECT * FROM pg_stat_activity;"

# 查看Redis状态
redis-cli info
redis-cli monitor

# 查看网络连接
netstat -tulpn | grep :8000
```

### 健康检查
```bash
# 检查所有服务健康状态
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health

# 批量健康检查脚本
#!/bin/bash
services=("8000" "8001" "8002" "8003" "8004")
for port in "${services[@]}"; do
  echo "Checking service on port $port..."
  curl -s http://localhost:$port/health | jq .
done
```

## 7. 数据管理

### 数据初始化
```bash
# 创建测试数据脚本
python scripts/init_test_data.py

# 导入景区数据
python scripts/import_scenic_areas.py --file data/scenic_areas.json

# 生成测试订单
python scripts/generate_test_orders.py --count 100
```

### 数据备份和恢复
```bash
# 备份PostgreSQL数据
pg_dump -h localhost -U postgres order_system > backup_$(date +%Y%m%d_%H%M%S).sql

# 备份Redis数据
redis-cli --rdb dump.rdb

# 恢复PostgreSQL数据
psql -h localhost -U postgres order_system < backup_20241030_153000.sql

# 数据迁移脚本
python scripts/migrate_data.py --from-env staging --to-env production
```

## 8. 部署命令

### Docker构建
```bash
# 构建单个服务镜像
cd order-service
docker build -t order-service:latest -f docker/Dockerfile .

# 构建所有服务镜像
docker-compose build

# 推送镜像到仓库
docker tag order-service:latest registry.example.com/order-service:latest
docker push registry.example.com/order-service:latest
```

### 生产环境部署
```bash
# 拉取最新镜像
docker-compose pull

# 滚动更新服务
docker-compose up -d --no-deps order-service

# 扩容服务
docker-compose up -d --scale order-service=3

# 查看服务状态
docker-compose ps
docker service ls  # 如果使用Docker Swarm
```

## 9. 故障排查

### 常见问题诊断
```bash
# 检查端口占用
lsof -i :8000
netstat -tulpn | grep :8000

# 检查磁盘空间
df -h
du -sh logs/

# 检查内存使用
free -h
ps aux --sort=-%mem | head

# 检查数据库连接
psql -h localhost -U postgres -d order_system -c "SELECT count(*) FROM pg_stat_activity;"

# 检查Redis连接
redis-cli ping
redis-cli info clients
```

### 日志分析
```bash
# 查找错误日志
grep -r "ERROR" logs/
grep -r "Exception" logs/

# 统计API调用次数
grep "POST /api/v1/orders" logs/access.log | wc -l

# 分析响应时间
awk '{print $NF}' logs/access.log | sort -n | tail -10

# 查找慢查询
grep "slow query" logs/postgresql.log
```

## 10. 维护命令

### 定期维护
```bash
# 清理Docker资源
docker system prune -f
docker volume prune -f
docker image prune -f

# 清理日志文件
find logs/ -name "*.log" -mtime +7 -delete
logrotate /etc/logrotate.d/order-system

# 数据库维护
psql -h localhost -U postgres -d order_system -c "VACUUM ANALYZE;"
psql -h localhost -U postgres -d order_system -c "REINDEX DATABASE order_system;"

# Redis维护
redis-cli FLUSHDB  # 清空当前数据库
redis-cli BGSAVE   # 后台保存数据
```

### 性能优化
```bash
# 分析慢查询
psql -h localhost -U postgres -d order_system -c "
  SELECT query, mean_time, calls 
  FROM pg_stat_statements 
  ORDER BY mean_time DESC 
  LIMIT 10;"

# 查看数据库索引使用情况
psql -h localhost -U postgres -d order_system -c "
  SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch 
  FROM pg_stat_user_indexes 
  ORDER BY idx_scan DESC;"

# Redis性能分析
redis-cli --latency-history
redis-cli --stat
```

## 11. 安全命令

### 安全检查
```bash
# 检查依赖漏洞
safety check
pip-audit

# 代码安全扫描
bandit -r .
semgrep --config=auto .

# Docker镜像安全扫描
docker scan order-service:latest
trivy image order-service:latest
```

### 证书管理
```bash
# 生成自签名证书（开发环境）
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# 检查证书有效期
openssl x509 -in cert.pem -text -noout | grep "Not After"

# 更新Let's Encrypt证书
certbot renew --dry-run
```

## 12. 自动化脚本

### 常用脚本
```bash
# 创建快速启动脚本
cat > start_dev.sh << 'EOF'
#!/bin/bash
echo "Starting development environment..."
docker-compose up -d postgres redis rabbitmq
sleep 10
cd order-service && uvicorn app.main:app --port 8001 --reload &
cd ../payment-service && uvicorn app.main:app --port 8002 --reload &
cd ../shipping-service && uvicorn app.main:app --port 8003 --reload &
cd ../api-gateway && uvicorn app.main:app --port 8000 --reload &
echo "All services started!"
EOF
chmod +x start_dev.sh

# 创建健康检查脚本
cat > health_check.sh << 'EOF'
#!/bin/bash
services=("8000:API Gateway" "8001:Order Service" "8002:Payment Service" "8003:Shipping Service")
for service in "${services[@]}"; do
  port=$(echo $service | cut -d: -f1)
  name=$(echo $service | cut -d: -f2)
  if curl -s http://localhost:$port/health > /dev/null; then
    echo "✓ $name (port $port) is healthy"
  else
    echo "✗ $name (port $port) is down"
  fi
done
EOF
chmod +x health_check.sh
```

## 总结

本文档涵盖了订单支付系统开发、测试、部署和维护的所有常用命令。建议开发团队：

1. 熟悉基本的开发调试命令
2. 掌握Docker和数据库操作
3. 学会使用监控和日志分析工具
4. 建立自动化脚本提高效率
5. 定期进行安全检查和性能优化

如有问题，请参考项目文档或联系开发团队。