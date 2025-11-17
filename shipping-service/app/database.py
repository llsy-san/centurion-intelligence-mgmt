"""
发货服务数据库模块
定义数据库连接和ORM模型 - PostgreSQL
"""
from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

from .config import config

# 创建异步数据库引擎 - PostgreSQL
engine = create_async_engine(
    config.database_url,
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


class ShippingModel(Base):
    """发货数据库模型 - PostgreSQL"""
    __tablename__ = "shipping"
    
    id = Column(String(50), primary_key=True, index=True)
    order_id = Column(String(50), nullable=False, index=True)
    tracking_number = Column(String(100), nullable=True, index=True)
    carrier = Column(String(50), nullable=True)
    shipping_address = Column(Text, nullable=False)
    phone = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="pending", index=True)
    shipped_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UserAssetModel(Base):
    """用户资产数据库模型 - PostgreSQL"""
    __tablename__ = "user_assets"
    
    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    asset_type = Column(String(20), nullable=False, index=True)
    asset_name = Column(String(200), nullable=False)
    asset_code = Column(String(500), nullable=False, unique=True, index=True)
    qr_code_url = Column(String(500), nullable=True)
    order_id = Column(String(50), nullable=True, index=True)
    status = Column(String(20), nullable=False, default="active", index=True)
    metadata = Column(JSON, nullable=True)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    used_at = Column(DateTime(timezone=True), nullable=True)
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