"""
AI Agent服务数据库模块
包含知识图谱和向量数据库配置
"""
from sqlalchemy import Column, String, DateTime, Text, Float, Integer, JSON
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

from .config import config

# 创建异步数据库引擎
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


class KnowledgeNodeModel(Base):
    """知识图谱节点模型"""
    __tablename__ = "knowledge_nodes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    node_type = Column(String(50), nullable=False, index=True)  # 节点类型：order, product, user, payment等
    entity_id = Column(String(100), nullable=False, index=True)  # 实体ID
    name = Column(String(200), nullable=False)  # 节点名称
    properties = Column(JSONB, nullable=False, default={})  # 节点属性
    embedding = Column(Text, nullable=True)  # 向量嵌入（JSON格式存储）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class KnowledgeRelationModel(Base):
    """知识图谱关系模型"""
    __tablename__ = "knowledge_relations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    source_node_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    target_node_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    relation_type = Column(String(50), nullable=False, index=True)  # 关系类型：contains, purchased, paid_by等
    properties = Column(JSONB, nullable=False, default={})  # 关系属性
    weight = Column(Float, default=1.0)  # 关系权重
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class VectorDocumentModel(Base):
    """向量文档模型"""
    __tablename__ = "vector_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    document_type = Column(String(50), nullable=False, index=True)  # 文档类型：faq, policy, manual等
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    metadata = Column(JSONB, nullable=False, default={})  # 文档元数据
    embedding = Column(Text, nullable=False)  # 向量嵌入（JSON格式存储）
    embedding_model = Column(String(100), nullable=False, default="text-embedding-ada-002")
    tags = Column(JSONB, nullable=False, default=[])  # 标签
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ChatSessionModel(Base):
    """聊天会话模型"""
    __tablename__ = "chat_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    session_type = Column(String(50), nullable=False, default="customer_service")  # 会话类型
    status = Column(String(20), nullable=False, default="active", index=True)  # active, closed
    context = Column(JSONB, nullable=False, default={})  # 会话上下文
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ChatMessageModel(Base):
    """聊天消息模型"""
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    metadata = Column(JSONB, nullable=False, default={})  # 消息元数据
    embedding = Column(Text, nullable=True)  # 消息向量嵌入
    created_at = Column(DateTime(timezone=True), server_default=func.now())


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
        print("🗄️ AI Agent数据库初始化完成")