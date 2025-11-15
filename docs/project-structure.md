# 项目结构说明

## 整体架构

订单支付系统采用微服务架构，主要包含以下组件：

```
order-payment-system/
├── shared/                     # 共享模块
│   ├── __init__.py
│   ├── models.py              # 数据模型定义
│   ├── config.py              # 配置管理
│   └── utils.py               # 工具函数
├── order-service/             # 订单服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # 服务入口
│   │   ├── database.py        # 数据库配置
│   │   ├── services.py        # 业务逻辑
│   │   └── routers/           # API路由
│   │       ├── __init__.py
│   │       └── orders.py      # 订单相关API
│   ├── tests/                 # 测试文件
│   │   └── test_orders.py
│   └── docker/                # Docker配置
│       └── Dockerfile
├── payment-service/           # 支付服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # 服务入口
│   │   ├── database.py        # 数据库配置
│   │   ├── services.py        # 业务逻辑
│   │   └── routers/           # API路由
│   │       ├── __init__.py
│   │       └── payments.py    # 支付相关API
│   ├── tests/                 # 测试文件
│   │   └── test_payments.py
│   └── docker/                # Docker配置
│       └── Dockerfile
├── shipping-service/          # 发货服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # 服务入口
│   │   ├── database.py        # 数据库配置
│   │   ├── services.py        # 业务逻辑
│   │   └── routers/           # API路由
│   │       ├── __init__.py
│   │       └── shipping.py    # 发货相关API
│   ├── tests/                 # 测试文件
│   │   └── test_shipping.py
│   └── docker/                # Docker配置
│       └── Dockerfile
├── api-gateway/               # API网关
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # 网关入口
│   │   ├── middleware.py      # 中间件
│   │   └── routers/           # 网关路由
│   │       ├── __init__.py
│   │       └── gateway.py     # 网关API
│   └── docker/                # Docker配置
│       └── Dockerfile
├── docker-compose/            # Docker Compose配置
│   └── docker-compose.yml
├── docs/                      # 文档目录
│   └── project-structure.md
├── requirements.txt           # Python依赖
├── .env.example              # 环境变量示例
├── .gitignore                # Git忽略文件
├── pytest.ini               # 测试配置
├── Makefile                  # 构建脚本
└── README.md                 # 项目说明
```

## 模块说明

### shared/ - 共享模块
包含各服务共用的代码：
- `models.py`: 定义数据模型和API请求/响应结构
- `config.py`: 配置管理，包括数据库、Redis、消息队列等配置
- `utils.py`: 工具函数，如ID生成、加密、JWT处理等

### order-service/ - 订单服务
负责订单相关的业务逻辑：
- 订单创建、查询、更新
- 订单状态管理
- 用户订单历史

### payment-service/ - 支付服务
负责支付相关的业务逻辑：
- 支付创建和处理
- 多种支付方式支持
- 退款处理

### shipping-service/ - 发货服务
负责发货相关的业务逻辑：
- 发货记录管理
- 物流状态跟踪
- 快递单号生成

### api-gateway/ - API网关
统一入口，负责：
- 请求路由转发
- 用户认证和授权
- 请求限流
- 日志记录

## 数据流

1. **订单创建流程**:
   ```
   客户端 -> API网关 -> 订单服务 -> 数据库
   ```

2. **支付流程**:
   ```
   客户端 -> API网关 -> 支付服务 -> 第三方支付 -> 订单服务(状态更新)
   ```

3. **发货流程**:
   ```
   支付成功 -> 发货服务 -> 物流系统 -> 订单服务(状态更新)
   ```

## 技术选型

- **Web框架**: FastAPI - 高性能异步框架
- **数据库**: PostgreSQL - 关系型数据库
- **缓存**: Redis - 内存数据库
- **消息队列**: RabbitMQ - 异步消息处理
- **容器化**: Docker + Docker Compose
- **API文档**: Swagger/OpenAPI - 自动生成文档
- **测试**: pytest - Python测试框架

## 部署架构

```
                    ┌─────────────┐
                    │   负载均衡   │
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │  API网关集群 │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────┴────┐      ┌─────┴─────┐      ┌────┴────┐
   │订单服务集群│      │支付服务集群│      │发货服务集群│
   └─────────┘      └───────────┘      └─────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    ┌──────┴──────┐
                    │  数据库集群  │
                    └─────────────┘
```

## 扩展性

系统设计考虑了以下扩展性：

1. **水平扩展**: 各服务可独立扩展
2. **服务拆分**: 可进一步拆分更细粒度的服务
3. **数据库分片**: 支持数据库水平分片
4. **缓存策略**: 多级缓存提升性能
5. **消息队列**: 异步处理提升吞吐量