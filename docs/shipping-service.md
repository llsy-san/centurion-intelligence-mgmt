# 物流服务文档

## 📋 服务概述

物流服务是百夫长智能管理系统的重要组成部分，负责订单发货、物流跟踪、库存管理、配送管理等功能，支持多家物流公司。

## 🏗️ 服务架构

```
物流请求 → 订单验证 → 物流分配 → 发货处理 → 状态跟踪
    ↓           ↓           ↓           ↓           ↓
  库存检查   →  地址验证  →  运费计算  →  单号生成  → 轨迹更新
  权限验证   →  配送规则  →  物流选择  →  信息推送  → 签收确认
```

## 🔧 技术栈

- **框架**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0 (异步)
- **数据库**: PostgreSQL 15
- **缓存**: Redis 7
- **HTTP客户端**: httpx (异步)
- **消息队列**: Celery + Redis
- **地图服务**: 高德地图API

## 📊 服务信息

| 属性 | 值 |
|------|-----|
| **服务名称** | shipping-service |
| **端口** | 8004 |
| **协议** | HTTP |
| **健康检查** | `/health` |
| **API文档** | `/docs` |
| **数据库表** | shipments, tracking_records, inventory |

## 🚀 快速启动

### 使用Docker

```bash
# 启动物流服务
make start-shipping

# 或直接使用脚本
./scripts/start-shipping-service.sh
```

### 本地开发

```bash
# 进入服务目录
cd shipping-service

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload --port 8004
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
  "cache": "connected",
  "logistics_providers": {
    "sf_express": "available",
    "sto_express": "available",
    "yto_express": "available"
  }
}
```

### 发货管理

#### 创建发货单
```http
POST /api/v1/shipments
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "order_id": "ORD202411160001",
  "shipping_address": {
    "name": "张三",
    "phone": "13800138000",
    "province": "北京市",
    "city": "北京市",
    "district": "朝阳区",
    "address": "xxx街道xxx号",
    "postal_code": "100000"
  },
  "items": [
    {
      "product_id": "prod001",
      "product_name": "商品名称",
      "quantity": 2,
      "weight": 0.5,
      "dimensions": {
        "length": 10,
        "width": 8,
        "height": 5
      }
    }
  ],
  "logistics_provider": "sf_express",
  "shipping_method": "standard",
  "insurance_value": 199.98,
  "remark": "易碎品，请小心处理"
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "发货单创建成功",
  "data": {
    "shipment_id": "SHIP202411160001",
    "order_id": "ORD202411160001",
    "tracking_number": "SF1234567890123",
    "logistics_provider": "sf_express",
    "shipping_method": "standard",
    "status": "pending",
    "estimated_delivery": "2024-11-18T18:00:00Z",
    "shipping_fee": 12.00,
    "created_at": "2024-11-16T10:00:00Z"
  }
}
```

#### 查询发货单列表
```http
GET /api/v1/shipments?page=1&size=10&status=shipped&order_id=ORD202411160001
Authorization: Bearer <access_token>
```

#### 查询发货单详情
```http
GET /api/v1/shipments/{shipment_id}
Authorization: Bearer <access_token>
```

**响应示例:**
```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "shipment_id": "SHIP202411160001",
    "order_id": "ORD202411160001",
    "tracking_number": "SF1234567890123",
    "logistics_provider": "sf_express",
    "status": "in_transit",
    "shipping_address": {
      "name": "张三",
      "phone": "13800138000",
      "full_address": "北京市朝阳区xxx街道xxx号"
    },
    "tracking_records": [
      {
        "timestamp": "2024-11-16T10:00:00Z",
        "status": "picked_up",
        "description": "快件已被收取",
        "location": "北京分拣中心"
      },
      {
        "timestamp": "2024-11-16T14:00:00Z",
        "status": "in_transit",
        "description": "快件正在运输途中",
        "location": "北京转运中心"
      }
    ],
    "estimated_delivery": "2024-11-18T18:00:00Z",
    "created_at": "2024-11-16T10:00:00Z"
  }
}
```

### 物流跟踪

#### 查询物流轨迹
```http
GET /api/v1/shipments/{shipment_id}/tracking
Authorization: Bearer <access_token>
```

#### 更新物流状态
```http
PUT /api/v1/shipments/{shipment_id}/status
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "status": "delivered",
  "location": "北京市朝阳区",
  "description": "快件已签收",
  "recipient": "张三",
  "signature_image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
}
```

#### 批量更新物流状态
```http
POST /api/v1/shipments/batch-update
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "updates": [
    {
      "tracking_number": "SF1234567890123",
      "status": "in_transit",
      "location": "上海转运中心",
      "description": "快件已到达转运中心"
    },
    {
      "tracking_number": "SF1234567890124",
      "status": "delivered",
      "location": "广州市天河区",
      "description": "快件已签收"
    }
  ]
}
```

### 库存管理

#### 查询库存
```http
GET /api/v1/inventory?product_id=prod001&warehouse_id=WH001
Authorization: Bearer <access_token>
```

**响应示例:**
```json
{
  "code": 200,
  "message": "查询成功",
  "data": [
    {
      "product_id": "prod001",
      "warehouse_id": "WH001",
      "warehouse_name": "北京仓库",
      "available_quantity": 100,
      "reserved_quantity": 20,
      "total_quantity": 120,
      "safety_stock": 10,
      "last_updated": "2024-11-16T10:00:00Z"
    }
  ]
}
```

#### 库存调整
```http
POST /api/v1/inventory/adjust
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "product_id": "prod001",
  "warehouse_id": "WH001",
  "adjustment_type": "increase",
  "quantity": 50,
  "reason": "采购入库",
  "reference_number": "PO202411160001"
}
```

#### 库存预留
```http
POST /api/v1/inventory/reserve
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "order_id": "ORD202411160001",
  "items": [
    {
      "product_id": "prod001",
      "warehouse_id": "WH001",
      "quantity": 2
    }
  ]
}
```

### 运费计算

#### 计算运费
```http
POST /api/v1/shipping/calculate-fee
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "origin": {
    "province": "北京市",
    "city": "北京市",
    "district": "朝阳区"
  },
  "destination": {
    "province": "上海市",
    "city": "上海市",
    "district": "浦东新区"
  },
  "items": [
    {
      "weight": 0.5,
      "dimensions": {
        "length": 10,
        "width": 8,
        "height": 5
      }
    }
  ],
  "logistics_provider": "sf_express",
  "shipping_method": "standard"
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "计算成功",
  "data": {
    "shipping_fee": 12.00,
    "insurance_fee": 2.00,
    "total_fee": 14.00,
    "estimated_delivery_days": 2,
    "estimated_delivery_time": "2024-11-18T18:00:00Z"
  }
}
```

## 📋 数据模型

### 发货单表 (shipments)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| shipment_id | VARCHAR(50) | 发货单号 |
| order_id | VARCHAR(50) | 订单ID |
| tracking_number | VARCHAR(100) | 物流单号 |
| logistics_provider | VARCHAR(50) | 物流公司 |
| shipping_method | VARCHAR(50) | 配送方式 |
| status | VARCHAR(20) | 发货状态 |
| shipping_address | JSON | 收货地址 |
| sender_address | JSON | 发货地址 |
| items | JSON | 商品信息 |
| shipping_fee | DECIMAL(10,2) | 运费 |
| insurance_fee | DECIMAL(10,2) | 保险费 |
| estimated_delivery | TIMESTAMP | 预计送达时间 |
| actual_delivery | TIMESTAMP | 实际送达时间 |
| remark | TEXT | 备注 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### 物流跟踪表 (tracking_records)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| shipment_id | VARCHAR(50) | 发货单号 |
| tracking_number | VARCHAR(100) | 物流单号 |
| status | VARCHAR(20) | 状态 |
| location | VARCHAR(200) | 位置 |
| description | TEXT | 描述 |
| operator | VARCHAR(100) | 操作员 |
| timestamp | TIMESTAMP | 时间戳 |
| created_at | TIMESTAMP | 创建时间 |

### 库存表 (inventory)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| product_id | VARCHAR(50) | 商品ID |
| warehouse_id | VARCHAR(50) | 仓库ID |
| available_quantity | INTEGER | 可用库存 |
| reserved_quantity | INTEGER | 预留库存 |
| total_quantity | INTEGER | 总库存 |
| safety_stock | INTEGER | 安全库存 |
| last_updated | TIMESTAMP | 最后更新时间 |

### 发货状态

| 状态 | 说明 |
|------|------|
| **pending** | 待发货 |
| **picked_up** | 已揽收 |
| **in_transit** | 运输中 |
| **out_for_delivery** | 派送中 |
| **delivered** | 已送达 |
| **failed_delivery** | 派送失败 |
| **returned** | 已退回 |
| **cancelled** | 已取消 |

## 🚚 物流公司集成

### 顺丰速运 (SF Express)

```python
# 顺丰API配置
SF_CONFIG = {
    "app_id": "your_app_id",
    "app_key": "your_app_key",
    "gateway": "https://bsp-oisp.sf-express.com/bsp-oisp/sfexpressService",
    "checkword": "your_checkword",
    "client_code": "your_client_code"
}

# 支持的服务类型
SF_SERVICES = {
    "standard": "标准快递",
    "express": "特快专递",
    "economy": "经济快递",
    "same_day": "当日达",
    "next_day": "次日达"
}
```

### 申通快递 (STO Express)

```python
# 申通API配置
STO_CONFIG = {
    "partner_id": "your_partner_id",
    "partner_key": "your_partner_key",
    "gateway": "https://open.sto.cn/api",
    "version": "1.0"
}
```

### 圆通速递 (YTO Express)

```python
# 圆通API配置
YTO_CONFIG = {
    "user_id": "your_user_id",
    "api_key": "your_api_key",
    "gateway": "https://open.yto.net.cn/api",
    "version": "1.0"
}
```

## 🔄 业务流程

### 发货流程

```mermaid
graph TD
    A[接收发货请求] --> B[验证订单状态]
    B --> C[检查库存]
    C --> D[选择物流公司]
    D --> E[计算运费]
    E --> F[创建发货单]
    F --> G[调用物流API]
    G --> H[获取物流单号]
    H --> I[更新发货状态]
    I --> J[通知用户]
```

### 物流跟踪流程

```mermaid
graph TD
    A[定时任务启动] --> B[获取待跟踪订单]
    B --> C[调用物流API]
    C --> D[解析轨迹信息]
    D --> E[更新跟踪记录]
    E --> F[检查状态变化]
    F --> G[发送状态通知]
    G --> H[更新订单状态]
```

## 📊 监控指标

### 物流指标

- **发货及时率**: 按时发货的订单比例
- **平均配送时间**: 从发货到送达的平均时间
- **签收率**: 成功签收的订单比例
- **物流异常率**: 出现异常的订单比例

### 库存指标

- **库存周转率**: 库存周转次数
- **缺货率**: 缺货商品的比例
- **库存准确率**: 系统库存与实际库存的匹配度
- **安全库存覆盖率**: 安全库存的覆盖情况

## 🛠️ 配置说明

### 环境变量

```bash
# 服务配置
SHIPPING_SERVICE_HOST=0.0.0.0
SHIPPING_SERVICE_PORT=8004
SHIPPING_SERVICE_DEBUG=false

# 数据库配置
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/centurion_db

# Redis配置
REDIS_URL=redis://localhost:6379/2

# 顺丰配置
SF_APP_ID=your_sf_app_id
SF_APP_KEY=your_sf_app_key
SF_CHECKWORD=your_sf_checkword
SF_CLIENT_CODE=your_sf_client_code

# 申通配置
STO_PARTNER_ID=your_sto_partner_id
STO_PARTNER_KEY=your_sto_partner_key

# 圆通配置
YTO_USER_ID=your_yto_user_id
YTO_API_KEY=your_yto_api_key

# 高德地图配置
AMAP_API_KEY=your_amap_api_key

# 默认仓库配置
DEFAULT_WAREHOUSE_ID=WH001
DEFAULT_SENDER_ADDRESS={"name":"发货仓库","phone":"400-123-4567","address":"北京市朝阳区xxx"}
```

### 物流公司配置

```python
# 物流公司配置
LOGISTICS_PROVIDERS = {
    "sf_express": {
        "name": "顺丰速运",
        "enabled": True,
        "priority": 1,
        "services": ["standard", "express", "same_day"],
        "coverage_areas": ["全国"],
        "api_timeout": 30
    },
    "sto_express": {
        "name": "申通快递",
        "enabled": True,
        "priority": 2,
        "services": ["standard", "economy"],
        "coverage_areas": ["全国"],
        "api_timeout": 30
    },
    "yto_express": {
        "name": "圆通速递",
        "enabled": True,
        "priority": 3,
        "services": ["standard", "economy"],
        "coverage_areas": ["全国"],
        "api_timeout": 30
    }
}
```

## 🐛 故障排除

### 常见问题

#### 1. 发货单创建失败
```bash
# 检查库存状态
curl http://localhost:8004/api/v1/inventory?product_id=prod001

# 查看服务日志
docker logs centurion-shipping-service

# 检查物流API连通性
curl -I https://bsp-oisp.sf-express.com/bsp-oisp/sfexpressService
```

#### 2. 物流跟踪更新失败
```bash
# 检查定时任务状态
docker exec centurion-redis redis-cli llen shipping_tracking_queue

# 查看跟踪日志
docker logs centurion-shipping-service | grep "tracking"

# 测试物流API
curl -X POST http://localhost:8004/api/v1/shipments/test-tracking
```

#### 3. 库存同步问题
```bash
# 检查库存一致性
curl http://localhost:8004/api/v1/inventory/check-consistency

# 查看库存调整日志
docker logs centurion-shipping-service | grep "inventory"

# 手动同步库存
curl -X POST http://localhost:8004/api/v1/inventory/sync
```

### 日志分析

```bash
# 查看发货日志
docker logs centurion-shipping-service | grep "shipment_created"

# 查看物流跟踪日志
docker logs centurion-shipping-service | grep "tracking_updated"

# 查看错误日志
docker logs centurion-shipping-service | grep ERROR
```

## 🔧 开发指南

### 添加新的物流公司

```python
# 在 services/logistics/ 中创建新的物流服务
class NewLogisticsProvider(BaseLogisticsProvider):
    def __init__(self, config: dict):
        self.config = config
    
    async def create_shipment(self, shipment_data: dict) -> dict:
        """创建发货单"""
        # 实现创建发货单逻辑
        pass
    
    async def track_shipment(self, tracking_number: str) -> List[dict]:
        """查询物流轨迹"""
        # 实现物流跟踪逻辑
        pass
    
    async def cancel_shipment(self, tracking_number: str) -> bool:
        """取消发货单"""
        # 实现取消发货单逻辑
        pass

# 在配置中注册新的物流公司
LOGISTICS_PROVIDERS["new_logistics"] = {
    "name": "新物流公司",
    "enabled": True,
    "provider_class": "NewLogisticsProvider"
}
```

### 自定义库存策略

```python
# 在 services/inventory/ 中实现
class CustomInventoryStrategy:
    async def check_availability(
        self, 
        product_id: str, 
        quantity: int, 
        warehouse_id: str = None
    ) -> bool:
        """检查库存可用性"""
        # 自定义库存检查逻辑
        pass
    
    async def reserve_inventory(
        self, 
        order_id: str, 
        items: List[dict]
    ) -> bool:
        """预留库存"""
        # 自定义库存预留逻辑
        pass
```


