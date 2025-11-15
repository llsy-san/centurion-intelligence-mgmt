# 代码规范文档

## 项目概述

本项目是基于微服务架构的订单支付系统，集成AI Agent、知识图谱和向量数据库，提供智能客服、数据分析和风险评估等功能。

## 技术栈

### 核心框架
- **后端框架**: FastAPI 0.104.1
- **异步运行时**: Uvicorn
- **数据验证**: Pydantic 2.5.0
- **数据库ORM**: SQLAlchemy 2.0.23 (异步)
- **数据库迁移**: Alembic 1.12.1

### 数据存储
- **主数据库**: PostgreSQL 15+
- **缓存**: Redis 5.0+
- **消息队列**: RabbitMQ (aio-pika)
- **知识图谱**: Neo4j 5.14+
- **向量搜索**: Elasticsearch 8.11+

### AI & 数据科学
- **机器学习**: scikit-learn, transformers
- **向量嵌入**: sentence-transformers
- **自然语言处理**: spaCy, jieba
- **知识图谱**: NetworkX
- **向量数据库**: ChromaDB, FAISS

### 工具库
- **HTTP客户端**: httpx, aiohttp
- **认证**: python-jose, passlib
- **日志**: structlog
- **监控**: prometheus-client
- **二维码**: qrcode, Pillow

## 代码规范

### 1. 项目结构

```
service-name/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI应用入口
│   ├── database.py          # 数据库配置和模型
│   ├── services.py          # 业务逻辑层
│   └── routers/
│       ├── __init__.py
│       └── service_name.py  # API路由定义
├── docker/
│   └── Dockerfile
├── tests/
│   └── test_*.py
└── requirements.txt
```

### 2. 命名规范

#### 文件和目录命名
- 使用小写字母和下划线：`user_service.py`
- 目录名使用小写：`routers/`, `services/`
- 测试文件以`test_`开头：`test_orders.py`

#### 变量和函数命名
```python
# 变量：小写字母和下划线
user_id = "user_001"
order_items = []
shipping_address = "北京市朝阳区"

# 函数：小写字母和下划线，动词开头
def create_order(order_data: OrderCreate) -> Order:
    pass

def get_user_by_id(user_id: str) -> Optional[User]:
    pass

def update_order_status(order_id: str, status: OrderStatus) -> bool:
    pass
```

#### 类命名
```python
# 类：大驼峰命名法
class OrderService:
    pass

class UserAssetModel:
    pass

class ThirdPartyShippingAPI:
    pass

# 枚举：大驼峰命名法
class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
```

#### 常量命名
```python
# 常量：全大写字母和下划线
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT = 30.0
API_VERSION = "v1"
```

### 3. 类型注解

#### 强制使用类型注解
```python
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

# 函数参数和返回值
async def create_shipping(
    shipping_data: ShippingCreate,
    order_items: Optional[List[OrderItem]] = None
) -> Shipping:
    pass

# 变量类型注解
user_assets: List[UserAsset] = []
metadata: Dict[str, Any] = {}
created_at: datetime = datetime.now()
```

#### Pydantic模型
```python
from pydantic import BaseModel, Field

class OrderCreate(BaseModel):
    user_id: str = Field(..., description="用户ID")
    items: List[OrderItem] = Field(..., description="订单商品列表")
    total_amount: Decimal = Field(..., gt=0, description="订单总金额")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }
```

### 4. 异步编程规范

#### 数据库操作
```python
# 使用异步数据库会话
async def get_order(db: AsyncSession, order_id: str) -> Optional[Order]:
    result = await db.execute(
        select(OrderModel).where(OrderModel.id == order_id)
    )
    return result.scalar_one_or_none()

# 事务处理
async def create_order_with_items(db: AsyncSession, order_data: OrderCreate) -> Order:
    try:
        # 创建订单
        db_order = OrderModel(**order_data.dict())
        db.add(db_order)
        
        # 创建订单项
        for item in order_data.items:
            db_item = OrderItemModel(**item.dict(), order_id=db_order.id)
            db.add(db_item)
        
        await db.commit()
        await db.refresh(db_order)
        return db_order
    except Exception:
        await db.rollback()
        raise
```

#### HTTP客户端
```python
import httpx

async def call_external_api(url: str, data: Dict[str, Any]) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json=data,
            timeout=30.0,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
```

### 5. 错误处理

#### 异常定义
```python
class OrderServiceError(Exception):
    """订单服务基础异常"""
    pass

class OrderNotFoundError(OrderServiceError):
    """订单不存在异常"""
    pass

class PaymentFailedError(OrderServiceError):
    """支付失败异常"""
    pass
```

#### 错误处理模式
```python
from fastapi import HTTPException, status

@router.post("/orders/")
async def create_order(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        order_service = OrderService(db)
        order = await order_service.create_order(order_data)
        return format_response(
            message="订单创建成功",
            data=order.dict()
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"创建订单失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="订单创建失败"
        )
```

### 6. 日志规范

#### 日志配置
```python
import structlog

logger = structlog.get_logger(__name__)

# 在服务中使用
class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = structlog.get_logger(self.__class__.__name__)
    
    async def create_order(self, order_data: OrderCreate) -> Order:
        self.logger.info("开始创建订单", user_id=order_data.user_id)
        try:
            # 业务逻辑
            order = await self._create_order_logic(order_data)
            self.logger.info("订单创建成功", order_id=order.id)
            return order
        except Exception as e:
            self.logger.error("订单创建失败", error=str(e))
            raise
```

#### 日志级别使用
```python
# DEBUG: 详细的调试信息
logger.debug("处理订单项", item_count=len(order_items))

# INFO: 一般信息，业务流程关键点
logger.info("订单状态更新", order_id=order_id, status=new_status)

# WARNING: 警告信息，不影响主流程
logger.warning("第三方API响应慢", response_time=response_time)

# ERROR: 错误信息，影响业务流程
logger.error("数据库连接失败", error=str(e))

# CRITICAL: 严重错误，系统级问题
logger.critical("服务启动失败", error=str(e))
```

### 7. 测试规范

#### 单元测试
```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_create_order(db_session: AsyncSession):
    """测试创建订单"""
    # Arrange
    order_data = OrderCreate(
        user_id="user_001",
        items=[
            OrderItem(
                product_id="prod_001",
                product_name="测试商品",
                quantity=1,
                unit_price=Decimal("99.99"),
                total_price=Decimal("99.99")
            )
        ],
        shipping_address="测试地址",
        phone="13800138000"
    )
    
    # Act
    order_service = OrderService(db_session)
    order = await order_service.create_order(order_data)
    
    # Assert
    assert order.id is not None
    assert order.user_id == "user_001"
    assert len(order.items) == 1
    assert order.status == OrderStatus.PENDING
```

#### API测试
```python
@pytest.mark.asyncio
async def test_create_order_api(client: AsyncClient):
    """测试创建订单API"""
    order_data = {
        "user_id": "user_001",
        "items": [
            {
                "product_id": "prod_001",
                "product_name": "测试商品",
                "quantity": 1,
                "unit_price": 99.99,
                "total_price": 99.99
            }
        ],
        "shipping_address": "测试地址",
        "phone": "13800138000"
    }
    
    response = await client.post("/api/v1/orders/", json=order_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "order_id" in data["data"]
```

### 8. 配置管理

#### 环境配置
```python
from pydantic import BaseSettings
import os

class ServiceConfig(BaseSettings):
    # 服务配置
    service_name: str = "order-service"
    host: str = "0.0.0.0"
    port: int = 8001
    debug: bool = False
    
    # 数据库配置
    db_host: str = "localhost"
    db_port: int = 5432
    db_username: str = "postgres"
    db_password: str = "password"
    db_database: str = "order_system"
    
    # Redis配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    
    # JWT配置
    jwt_secret_key: str = "your-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

### 9. API设计规范

#### RESTful API设计
```python
# 资源命名：使用复数名词
GET    /api/v1/orders/              # 获取订单列表
POST   /api/v1/orders/              # 创建订单
GET    /api/v1/orders/{order_id}    # 获取特定订单
PUT    /api/v1/orders/{order_id}    # 更新订单
DELETE /api/v1/orders/{order_id}    # 删除订单

# 子资源
GET    /api/v1/orders/{order_id}/items/     # 获取订单项
POST   /api/v1/orders/{order_id}/items/     # 添加订单项

# 操作资源
POST   /api/v1/orders/{order_id}/cancel     # 取消订单
POST   /api/v1/orders/{order_id}/pay        # 支付订单
```

#### 响应格式
```python
# 统一响应格式
class BaseResponse(BaseModel):
    success: bool = True
    message: str = "操作成功"
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None

# 成功响应
{
    "success": true,
    "message": "订单创建成功",
    "data": {
        "order_id": "ORD20241030001",
        "status": "pending",
        "created_at": "2024-10-30T15:30:00Z"
    }
}

# 错误响应
{
    "success": false,
    "message": "订单不存在",
    "error_code": "ORDER_NOT_FOUND"
}
```

### 10. 性能优化

#### 数据库查询优化
```python
# 使用索引
class OrderModel(Base):
    __tablename__ = "orders"
    
    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)  # 添加索引
    status = Column(String(20), nullable=False, index=True)   # 添加索引
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

# 批量查询
async def get_orders_by_user(db: AsyncSession, user_id: str) -> List[Order]:
    result = await db.execute(
        select(OrderModel)
        .where(OrderModel.user_id == user_id)
        .options(selectinload(OrderModel.items))  # 预加载关联数据
        .order_by(OrderModel.created_at.desc())
        .limit(100)
    )
    return result.scalars().all()
```

#### 缓存策略
```python
import redis.asyncio as redis

class CacheService:
    def __init__(self):
        self.redis = redis.from_url("redis://localhost:6379")
    
    async def get_order_cache(self, order_id: str) -> Optional[Dict[str, Any]]:
        cached = await self.redis.get(f"order:{order_id}")
        if cached:
            return json.loads(cached)
        return None
    
    async def set_order_cache(self, order_id: str, order_data: Dict[str, Any], ttl: int = 3600):
        await self.redis.setex(
            f"order:{order_id}",
            ttl,
            json.dumps(order_data, default=str)
        )
```

### 11. 安全规范

#### 输入验证
```python
from pydantic import validator, Field

class OrderCreate(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=50, regex=r'^[a-zA-Z0-9_]+$')
    phone: str = Field(..., regex=r'^1[3-9]\d{9}$')  # 手机号验证
    
    @validator('items')
    def validate_items(cls, v):
        if not v or len(v) == 0:
            raise ValueError('订单项不能为空')
        if len(v) > 100:
            raise ValueError('订单项数量不能超过100')
        return v
```

#### 敏感信息处理
```python
# 不要在日志中记录敏感信息
logger.info("用户登录", user_id=user_id)  # ✓ 正确
logger.info("用户登录", password=password)  # ✗ 错误

# 数据库中敏感字段加密
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)
```

## 代码审查清单

### 提交前检查
- [ ] 代码符合命名规范
- [ ] 添加了适当的类型注解
- [ ] 异常处理完整
- [ ] 添加了必要的日志
- [ ] 编写了单元测试
- [ ] 更新了API文档
- [ ] 检查了安全性问题
- [ ] 性能考虑合理

### 代码质量工具
```bash
# 代码格式化
black .

# 导入排序
isort .

# 代码检查
flake8 .

# 类型检查
mypy .

# 测试覆盖率
pytest --cov=app tests/
```

## 最佳实践

1. **单一职责原则**: 每个类和函数只负责一个功能
2. **依赖注入**: 使用FastAPI的依赖注入系统
3. **配置外部化**: 所有配置通过环境变量管理
4. **错误处理**: 统一的错误处理和响应格式
5. **日志记录**: 结构化日志，便于监控和调试
6. **测试驱动**: 编写测试用例，保证代码质量
7. **文档完整**: API文档和代码注释完整
8. **性能监控**: 添加性能指标和监控
9. **安全第一**: 输入验证、权限控制、敏感信息保护
10. **持续集成**: 自动化测试和部署流程