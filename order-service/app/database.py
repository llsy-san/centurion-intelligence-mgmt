"""
订单服务数据库模块
定义数据库连接和ORM模型 - PostgreSQL
"""
from sqlalchemy import Column, String, DateTime, Text, Numeric, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

from .config import OrderServiceConfig

# 初始化配置
config = OrderServiceConfig()

# 创建异步数据库引擎 - PostgreSQL
engine = create_async_engine(
    config.database.url,
    echo=config.debug,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 创建基础模型类
Base = declarative_base()


class OrderModel(Base):
    """订单数据库模型 - PostgreSQL"""
    __tablename__ = "orders"
    
    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    items = Column(JSONB, nullable=False)  # PostgreSQL JSONB类型
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), nullable=False, default="pending", index=True)
    shipping_address = Column(Text, nullable=False)
    phone = Column(String(20), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


async def get_db() -> AsyncSession:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """初始化数据库"""
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)