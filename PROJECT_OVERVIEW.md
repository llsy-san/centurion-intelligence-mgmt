# 百夫长智能管理系统项目概览
## Centurion Intelligence Management System

## 项目简介

百夫长智能管理系统是一个基于微服务架构的现代化智能订单处理和支付管理平台。系统支持多租户、多渠道的订单处理，具备完善的支付、物流和数据同步功能，集成AI智能分析能力。

## 🏗️ 系统架构

### 微服务架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │    │  Order Service  │    │ Payment Service │
│     (8000)      │    │     (8001)      │    │     (8002)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Shipping Service│    │Task Scheduler   │    │  AI Agent       │
│     (8003)      │    │     (8004)      │    │     (8005)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 核心服务

1. **API Gateway (8000)** - API网关服务
   - 统一入口和路由
   - 身份认证和授权
   - 请求限流和监控

2. **Order Service (8001)** - 订单服务
   - 订单创建和管理
   - 订单状态跟踪
   - 通用查询接口

3. **Payment Service (8002)** - 支付服务
   - 多渠道支付处理
   - 支付状态管理
   - 退款处理

4. **Shipping Service (8003)** - 物流服务
   - 物流信息管理
   - 配送状态跟踪
   - 地址管理

5. **Task Scheduler Service (8004)** - 定时任务服务 ⭐
   - 第三方数据同步
   - 定时任务调度
   - 数据统计分析

6. **AI Agent Service (8005)** - AI智能体服务
   - 智能客服
   - 数据分析
   - 决策支持

## 🆕 新增定时任务服务

### 主要功能
- **数据同步**: 从第三方系统自动同步订单和产品数据
- **定时调度**: 支持灵活的定时任务配置
- **数据查询**: 提供丰富的查询和统计接口
- **监控告警**: 完善的任务执行监控

### 数据同步流程
1. **订单同步**: 获取第三方订单列表，处理订单状态映射
2. **产品同步**: 同步产品信息、核验记录和退款数据
3. **客户同步**: 处理客户信息和消费记录
4. **状态更新**: 实时更新订单和产品状态

### 数据表设计
- `order_sync`: 订单同步表
- `order_product_sync`: 订单产品同步表
- `product_detail`: 产品明细表
- `organization`: 组织客户表
- `sync_task_log`: 同步任务日志表

## 🛠️ 技术栈

### 后端技术
- **框架**: FastAPI + Python 3.11
- **数据库**: PostgreSQL + Redis
- **ORM**: SQLAlchemy (异步)
- **任务调度**: APScheduler
- **容器化**: Docker + Docker Compose

### 开发工具
- **代码质量**: Black, Flake8, MyPy
- **测试**: Pytest + Coverage
- **文档**: Swagger/OpenAPI
- **监控**: Prometheus + Grafana

## 📁 项目结构

```
centurion-intelligence-mgmt/
├── api-gateway/              # API网关服务
├── order-service/            # 订单服务
├── payment-service/          # 支付服务
├── shipping-service/         # 物流服务
├── task-scheduler-service/   # 定时任务服务 ⭐
├── ai-agent-service/         # AI智能体服务
├── shared/                   # 共享模块
│   ├── config.py            # 配置管理
│   ├── models.py            # 数据模型
│   └── utils.py             # 工具函数
├── docker-compose/           # Docker配置
├── scripts/                  # 部署脚本
├── docs/                     # 文档
└── tests/                    # 测试代码
```

## 🚀 快速开始

### 1. 环境准备
```bash
# 克隆项目
git clone <repository-url>
cd centurion-intelligence-mgmt

# 安装依赖
make install
```

### 2. 启动定时任务服务
```bash
# 使用脚本启动
./scripts/start-task-scheduler.sh

# 或使用Makefile
make run-tasks
```

### 3. 验证服务
```bash
# 检查服务状态
curl http://localhost:8004/health

# 查看API文档
open http://localhost:8004/docs
```

## 📊 数据同步配置

### 第三方API配置
```env
THIRD_PARTY_API_URL=https://api.third-party.com
THIRD_PARTY_API_KEY=your-api-key
```

### 同步频率设置
- **增量同步**: 每小时执行
- **全量同步**: 每日2点执行

### 数据映射规则
- 订单编号: `BFZ + 年月日 + 6位序号`
- 状态映射: 外部状态 → 内部状态
- 客户信息: 微信OpenID → 客户ID

## 🔧 开发指南

### 本地开发
```bash
# 启动开发环境
cd task-scheduler-service
python -m app.main

# 运行测试
pytest tests/ -v

# 代码检查
make lint
```

### API测试
```bash
# 手动触发同步
curl -X POST http://localhost:8004/api/v1/tasks/sync/orders/manual

# 查询订单
curl "http://localhost:8004/api/v1/sync/orders?page=1&page_size=10"

# 获取统计信息
curl http://localhost:8004/api/v1/sync/statistics
```

## 📈 监控和运维

### 健康检查
- 服务健康: `/health`
- 任务状态: `/api/v1/tasks/status`
- 同步日志: `/api/v1/tasks/logs`

### 日志管理
```bash
# 查看服务日志
docker-compose logs -f task-scheduler-service

# 查看同步日志
curl http://localhost:8004/api/v1/tasks/logs
```

### 数据备份
```bash
# 备份数据库
make backup-db

# 恢复数据库
make restore-db
```

## 🔒 安全说明

### 数据安全
- API密钥加密存储
- 敏感信息脱敏处理
- 数据传输HTTPS加密

### 访问控制
- JWT令牌认证
- 角色权限管理
- API访问限流

## 📋 部署清单

### 生产环境部署
- [ ] 配置环境变量
- [ ] 设置数据库连接
- [ ] 配置第三方API
- [ ] 启动服务容器
- [ ] 验证服务状态
- [ ] 配置监控告警

### 数据迁移
- [ ] 备份现有数据
- [ ] 执行数据库迁移
- [ ] 验证数据完整性
- [ ] 启动同步任务

## 🎯 未来规划

### 功能扩展
- [ ] 支持更多第三方系统
- [ ] 增加实时数据推送
- [ ] 优化同步性能
- [ ] 增加数据分析功能

### 技术优化
- [ ] 引入消息队列
- [ ] 实现分布式锁
- [ ] 优化数据库性能
- [ ] 增加缓存层


**版本**: v1.0.0  
**更新时间**: 2025-01-15  
**维护团队**: 百夫长智能管理系统开发团队