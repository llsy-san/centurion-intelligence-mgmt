# 订单服务文档

## 📋 服务概述

订单服务是百夫长智能管理系统的核心业务服务，负责订单的创建、查询、更新、状态管理等功能。

## 🏗️ 服务架构

```
订单请求 → 订单验证 → 库存检查 → 订单创建 → 状态更新
    ↓           ↓           ↓           ↓           ↓
  参数校验   →  业务规则  →  库存扣减  →  数据持久化 → 事件通知
  权限检查   →  价格计算  →  支付创建  →  订单编号  → 状态同步
```

## 🔧 技术栈

- **框架**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0 (异步)
- **数据库**: PostgreSQL 15
- **缓存**: Redis 7
- **消息队列**: Celery + Redis
- **数据验证**: Pydantic 2.0+

## 📊 服务信息

| 属性 | 值 |
|------|-----|
| **服务名称** | order-service |
| **端口** | 8002 |
| **协议** | HTTP |
| **健康检查** | `/health` |
| **API文档** | `/docs` |
| **数据库表** | orders, order_items |

## 🚀 快速启动

### 使用Docker

```bash
# 启动订单服务
make start-order

# 或直接使用脚本
./scripts/start-order-service.sh
```

### 本地开发

```bash
# 进入服务目录
cd order-service

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload --port 8002
```

## 📡 API接口

### 健康检查

```http
GET /health
```

**响应示例:**
```json
{
  "status": "healthy",
  "timestamp": "2024-11-16T10:00:00Z",
  "database": "connected",
  "cache": "connected"
}
```

### 订单管理

#### 创建订单
```http
POST /api/v1/orders
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "user_id": "user123",
  "items": [
    {
      "product_id": "prod001",
      "product_name": "商品名称",
      "quantity": 2,
      "unit_price": 99.99
    }
  ],
  "shipping_address": {
    "name": "张三",
    "phone": "13800138000",
    "address": "北京市朝阳区xxx街道xxx号"
  },
  "payment_method": "alipay",
  "remark": "订单备注"
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "订单创建成功",
  "data": {
    "order_id": "ORD202411160001",
    "order_number": "ORD202411160001",
    "user_id": "user123",
    "total_amount": 199.98,
    "status": "pending",
    "created_at": "2024-11-16T10:00:00Z",
    "items": [
      {
        "product_id": "prod001",
        "product_name": "商品名称",
        "quantity": 2,
        "unit_price": 99.99,
        "total_price": 199.98
      }
    ]
  }
}
```

#### 查询订单列表
```http
GET /api/v1/orders?page=1&size=10&status=pending&user_id=user123
Authorization: Bearer <access_token>
```

**响应示例:**
```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "total": 100,
    "page": 1,
    "size": 10,
    "pages": 10,
    "items": [
      {
        "order_id": "ORD202411160001",
        "order_number": "ORD202411160001",
        "user_id": "user123",
        "total_amount": 199.98,
        "status": "pending",
        "created_at": "2024-11-16T10:00:00Z"
      }
    ]
  }
}
```

#### 查询订单详情
```http
GET /api/v1/orders/{order_id}
Authorization: Bearer <access_token>
```

#### 更新订单状态
```http
PUT /api/v1/orders/{order_id}/status
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "status": "paid",
  "remark": "支付完成"
}
```

#### 取消订单
```http
DELETE /api/v1/orders/{order_id}
Authorization: Bearer <access_token>

{
  "reason": "用户主动取消",
  "refund_amount": 199.98
}
```

### 订单统计

#### 订单统计信息
```http
GET /api/v1/orders/statistics?start_date=2024-11-01&end_date=2024-11-16
Authorization: Bearer <access_token>
```

**响应示例:**
```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "total_orders": 1000,
    "total_amount": 99999.99,
    "status_distribution": {
      "pending": 100,
      "paid": 800,
      "shipped": 80,
      "delivered": 15,
      "cancelled": 5
    },
    "daily_statistics": [
      {
        "date": "2024-11-16",
        "orders": 50,
        "amount": 4999.99
      }
    ]
  }
}
```

## 📋 数据模型

### 订单表 (orders)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| order_number | VARCHAR(50) | 订单编号 |
| user_id | VARCHAR(50) | 用户ID |
| total_amount | DECIMAL(10,2) | 订单总金额 |
| status | VARCHAR(20) | 订单状态 |
| payment_method | VARCHAR(20) | 支付方式 |
| shipping_address | JSON | 收货地址 |
| remark | TEXT | 订单备注 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### 订单项表 (order_items)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| order_id | UUID | 订单ID |
| product_id | VARCHAR(50) | 商品ID |
| product_name | VARCHAR(200) | 商品名称 |
| quantity | INTEGER | 数量 |
| unit_price | DECIMAL(10,2) | 单价 |
| total_price | DECIMAL(10,2) | 小计 |
| created_at | TIMESTAMP | 创建时间 |

### 订单状态

| 状态 | 说明 |
|------|------|
| **pending** | 待支付 |
| **paid** | 已支付 |
| **shipped** | 已发货 |
| **delivered** | 已送达 |
| **cancelled** | 已取消 |
| **refunded** | 已退款 |

## 🔄 业务流程

### 订单创建流程

```mermaid
graph TD
    A[接收订单请求] --> B[参数验证]
    B --> C[用户权限检查]
    C --> D[商品信息验证]
    D --> E[库存检查]
    E --> F[价格计算]
    F --> G[创建订单记录]
    G --> H[扣减库存]
    H --> I[创建支付记录]
    I --> J[发送订单事件]
    J --> K[返回订单信息]
```

### 订单状态流转

```mermaid
graph LR
    A[pending] --> B[paid]
    B --> C[shipped]
    C --> D[delivered]
    A --> E[cancelled]
    B --> E
    B --> F[refunded]
```

## 🔐 权限控制

### 访问权限

| 操作 | 权限要求 |
|------|----------|
| **创建订单** | 登录用户 |
| **查询自己的订单** | 订单所有者 |
| **查询所有订单** | 管理员 |
| **更新订单状态** | 管理员/系统 |
| **取消订单** | 订单所有者/管理员 |
| **订单统计** | 管理员 |

### 数据权限

- 普通用户只能查看和操作自己的订单
- 管理员可以查看和操作所有订单
- 系统服务可以更新订单状态

## 📊 性能优化

### 数据库优化

```sql
-- 订单表索引
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_orders_order_number ON orders(order_number);

-- 订单项表索引
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
```

### 缓存策略

```python
# 订单详情缓存 (5分钟)
@cache(expire=300)
async def get_order_detail(order_id: str):
    pass

# 用户订单列表缓存 (1分钟)
@cache(expire=60)
async def get_user_orders(user_id: str, page: int, size: int):
    pass

# 订单统计缓存 (10分钟)
@cache(expire=600)
async def get_order_statistics(start_date: date, end_date: date):
    pass
```

### 分页优化

```python
# 使用游标分页提高大数据量查询性能
async def get_orders_cursor(
    cursor: Optional[str] = None,
    limit: int = 20
):
    query = select(Order)
    if cursor:
        query = query.where(Order.created_at < cursor)
    query = query.order_by(Order.created_at.desc()).limit(limit)
    return await db.execute(query)
```

## 🔔 事件通知

### 订单事件

订单服务会发送以下事件到消息队列：

| 事件类型 | 说明 | 数据 |
|----------|------|------|
| **order.created** | 订单创建 | 订单详情 |
| **order.paid** | 订单支付 | 订单ID、支付信息 |
| **order.shipped** | 订单发货 | 订单ID、物流信息 |
| **order.delivered** | 订单送达 | 订单ID、签收信息 |
| **order.cancelled** | 订单取消 | 订单ID、取消原因 |

### 事件消费

其他服务可以订阅这些事件：

```python
# 支付服务监听订单创建事件
@celery.task
def handle_order_created(order_data):
    # 创建支付记录
    create_payment_record(order_data)

# 物流服务监听订单支付事件
@celery.task
def handle_order_paid(order_data):
    # 创建物流记录
    create_shipping_record(order_data)
```

## 🛠️ 配置说明

### 环境变量

```bash
# 服务配置
ORDER_SERVICE_HOST=0.0.0.0
ORDER_SERVICE_PORT=8002
ORDER_SERVICE_DEBUG=false

# 数据库配置
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/centurion_db

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 业务配置
ORDER_NUMBER_PREFIX=ORD
ORDER_EXPIRE_MINUTES=30
MAX_ORDER_ITEMS=50

# 库存服务配置
INVENTORY_SERVICE_URL=http://localhost:8007
INVENTORY_CHECK_TIMEOUT=5

# 支付服务配置
PAYMENT_SERVICE_URL=http://localhost:8003
PAYMENT_CREATE_TIMEOUT=10
```

### 业务规则配置

```python
# 订单配置
ORDER_CONFIG = {
    "max_items_per_order": 50,
    "min_order_amount": 0.01,
    "max_order_amount": 99999.99,
    "order_expire_minutes": 30,
    "auto_cancel_minutes": 1440,  # 24小时
}

# 状态流转规则
STATUS_TRANSITIONS = {
    "pending": ["paid", "cancelled"],
    "paid": ["shipped", "refunded", "cancelled"],
    "shipped": ["delivered", "cancelled"],
    "delivered": ["refunded"],
    "cancelled": [],
    "refunded": []
}
```

## 🐛 故障排除

### 常见问题

#### 1. 订单创建失败
```bash
# 检查数据库连接
docker exec centurion-postgres pg_isready -U postgres

# 查看服务日志
docker logs centurion-order-service

# 检查库存服务
curl http://localhost:8007/health
```

#### 2. 订单状态更新失败
```bash
# 检查Redis连接
docker exec centurion-redis redis-cli ping

# 查看事件队列
docker exec centurion-redis redis-cli llen order_events

# 检查权限配置
curl -H "Authorization: Bearer <token>" http://localhost:8002/api/v1/orders/test
```

#### 3. 查询性能问题
```bash
# 检查数据库索引
docker exec centurion-postgres psql -U postgres -d centurion_db -c "\d orders"

# 查看慢查询日志
docker logs centurion-order-service | grep "slow_query"

# 检查缓存命中率
docker exec centurion-redis redis-cli info stats
```

### 日志分析

```bash
# 查看订单创建日志
docker logs centurion-order-service | grep "order_created"

# 查看错误日志
docker logs centurion-order-service | grep ERROR

# 查看性能日志
docker logs centurion-order-service | grep "response_time"
```

## 🔧 开发指南

### 添加新的订单状态

```python
# 在 models.py 中添加新状态
class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    NEW_STATUS = "new_status"  # 新状态

# 更新状态流转规则
STATUS_TRANSITIONS = {
    # ... 现有规则
    "new_status": ["delivered", "cancelled"]
}
```

### 添加订单验证规则

```python
# 在 services/order_service.py 中添加
class OrderValidator:
    @staticmethod
    async def validate_custom_rule(order_data: dict) -> bool:
        # 自定义验证逻辑
        return True
    
    @staticmethod
    async def validate_order(order_data: dict) -> List[str]:
        errors = []
        
        # 执行各种验证
        if not await OrderValidator.validate_custom_rule(order_data):
            errors.append("自定义验证失败")
            
        return errors
```

### 自定义订单编号生成

```python
# 在 utils/order_utils.py 中实现
class OrderNumberGenerator:
    @staticmethod
    def generate_order_number() -> str:
        # 自定义编号生成逻辑
        prefix = "ORD"
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = "".join(random.choices(string.digits, k=4))
        return f"{prefix}{timestamp}{random_suffix}"
```