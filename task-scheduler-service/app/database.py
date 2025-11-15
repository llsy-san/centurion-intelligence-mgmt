"""
定时任务服务数据库模块
定义订单同步相关的数据库模型
"""
from sqlalchemy import Column, String, DateTime, Text, Numeric, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import sys
import os

# 添加共享模块到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))

from config import TaskSchedulerConfig

# 初始化配置
config = TaskSchedulerConfig()

# 创建异步数据库引擎
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


class OrderSyncModel(Base):
    """订单同步表"""
    __tablename__ = "order_sync"
    
    # 基础字段
    order_no = Column(String(50), primary_key=True, comment="订单编号 BFZ+年月日+6位自增数字")
    external_no = Column(String(100), nullable=False, unique=True, index=True, comment="外部编号 来源系统的唯一编号")
    external_order_status = Column(String(50), comment="外部订单状态")
    order_type = Column(String(20), default="WEMINI", comment="订单类型 WEMINI/APP/OTHER")
    tenant_id = Column(String(50), default="default", comment="租户ID")
    tenant_name = Column(String(100), default="默认", comment="租户名称")
    customer_id = Column(String(100), comment="客户ID")
    
    # 时间字段
    create_time = Column(DateTime(timezone=True), comment="创建时间")
    pay_type = Column(String(20), default="WECHAT", comment="支付类型 WECHAT/ALIPAY/OTHER")
    pay_time = Column(DateTime(timezone=True), comment="支付时间")
    arrival_time = Column(DateTime(timezone=True), comment="到账时间")
    pay_status = Column(String(20), comment="支付状态")
    order_status = Column(String(20), comment="订单状态 UNPAY/UNUSE/USING/COMPT/REFD/UNDO")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 支付相关
    pay_no = Column(String(100), comment="支付单号")
    mailing_address = Column(Text, comment="邮寄地址")
    mailing_status = Column(String(50), comment="邮寄状态")
    hotel_confirm_no = Column(String(100), comment="订单确认单号")
    
    # 派生数据
    product_count = Column(Integer, default=0, comment="产品数量")
    avg_price = Column(Numeric(10, 2), default=0, comment="平均单价")
    order_amount = Column(Numeric(10, 2), default=0, comment="订单金额")
    refund_amount = Column(Numeric(10, 2), default=0, comment="退款金额")
    settlement_amount = Column(Numeric(10, 2), default=0, comment="结算金额")
    channel_fee = Column(Numeric(10, 2), default=0, comment="渠道/分销费用")
    
    # 系统字段
    sync_status = Column(String(20), default="PENDING", comment="同步状态")
    sync_time = Column(DateTime(timezone=True), comment="同步时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="记录创建时间")


class OrderProductSyncModel(Base):
    """订单产品同步表"""
    __tablename__ = "order_product_sync"
    
    # 基础字段
    id = Column(Integer, primary_key=True, autoincrement=True, comment="订单产品编号")
    order_no = Column(String(50), ForeignKey('order_sync.order_no'), nullable=False, comment="订单编号")
    product_id = Column(String(50), default="default", comment="产品ID")
    product_name = Column(String(200), default="默认", comment="产品名称")
    tenant_id = Column(String(50), default="default", comment="租户ID")
    tenant_name = Column(String(100), default="默认", comment="租户名称")
    external_no = Column(String(100), nullable=False, index=True, comment="外部编号 m开头")
    
    # 分类字段
    category_level1 = Column(String(100), default="南京夫子庙", comment="一级品类/业务领域")
    category_level2 = Column(String(100), comment="二级品类")
    category_level3 = Column(String(100), comment="三级品类")
    category_level4 = Column(String(100), default="联票", comment="四级品类")
    category_level5 = Column(String(100), comment="五级品类")
    
    # 价格和渠道
    channel_price = Column(Numeric(10, 2), comment="渠道价格")
    channel_commission_rate = Column(Numeric(5, 4), default=0.0038, comment="渠道佣金率")
    available_start_time = Column(DateTime(timezone=True), comment="可用开始时间")
    available_end_time = Column(DateTime(timezone=True), comment="可用结束时间")
    channel_id = Column(String(50), comment="渠道/分销ID")
    channel_name = Column(String(100), default="微信小程序", comment="渠道/分销名称")
    
    # 客户信息
    quantity = Column(Integer, default=1, comment="数量")
    user_no = Column(String(100), comment="用户编号")
    customer_name = Column(String(100), comment="客户名称")
    customer_phone = Column(String(20), comment="客户联系方式")
    customer_id_card = Column(String(50), comment="客户唯一识别码")
    flexible_collection = Column(Numeric(10, 2), comment="灵活代收")
    
    # 状态字段
    product_status = Column(String(20), comment="产品状态 UNPAY/UNUSE/USING/COMPT/REFD/UNDO")
    verify_method = Column(String(20), comment="核验方式 CHECK/FCHECK")
    verify_device = Column(String(50), default="扫码机", comment="核验设备")
    verify_device_name = Column(String(100), comment="核验设备账号名称")
    verify_id = Column(String(100), comment="核验ID")
    
    # 退款相关
    refund_device_name = Column(String(100), comment="退款设备名称")
    refund_account_id = Column(String(100), comment="退款账号ID")
    refund_device = Column(String(50), comment="退款设备")
    refund_method = Column(String(20), comment="退款方式 REFD/FREFD")
    apply_refund_amount = Column(Numeric(10, 2), comment="申请退款金额")
    actual_refund_amount = Column(Numeric(10, 2), comment="实际退款金额")
    refund_status = Column(String(20), comment="退款状态")
    refund_no = Column(String(100), comment="退款编号")
    refund_reason = Column(String(200), comment="退款原因")
    refund_time = Column(DateTime(timezone=True), comment="退款时间")
    
    # 时间字段
    use_time = Column(DateTime(timezone=True), comment="使用时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 地址相关
    mailing_address = Column(Text, comment="邮寄地址")
    express_no = Column(String(100), comment="邮寄快递单号")
    refund_address = Column(Text, comment="退款地址")
    refund_express_no = Column(String(100), comment="退款快递单号")
    
    # 派生数据
    channel_product_commission = Column(Numeric(10, 2), comment="渠道/分销产品佣金")
    
    # 关联关系
    order = relationship("OrderSyncModel", backref="products")


class ProductModel(Base):
    """产品明细表"""
    __tablename__ = "product_detail"
    
    product_id = Column(String(50), primary_key=True, comment="产品ID")
    product_name = Column(String(200), nullable=False, comment="产品名称")
    category_level1 = Column(String(100), comment="一级品类/业务领域")
    category_level2 = Column(String(100), comment="二级品类")
    category_level3 = Column(String(100), comment="三级品类")
    category_level4 = Column(String(100), comment="四级品类")
    category_level5 = Column(String(100), comment="五级品类")
    product_price = Column(Numeric(10, 2), comment="产品价格")
    product_attrs = Column(JSONB, comment="产品属性")
    purchase_time = Column(DateTime(timezone=True), comment="可购时间")
    available_time = Column(DateTime(timezone=True), comment="可用时间")
    product_spec = Column(String(500), comment="产品规格")
    tenant_id = Column(String(50), comment="租户ID")
    tenant_name = Column(String(100), comment="租户名称")
    inventory = Column(Integer, default=0, comment="库存")
    tags = Column(String(500), comment="标签")
    del_yn = Column(String(1), default="N", comment="删除标识")
    remarks = Column(Text, comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")


class OrganizationModel(Base):
    """组织表"""
    __tablename__ = "organization"
    
    org_id = Column(String(50), primary_key=True, comment="组织ID")
    org_name = Column(String(200), nullable=False, comment="组织名称")
    org_type = Column(String(50), comment="组织分类")
    customer_name = Column(String(100), comment="客户名称")
    unique_id = Column(String(100), comment="唯一标识")
    channel_user_id = Column(String(100), comment="来源渠道用户唯一标识")
    contact_info = Column(String(200), comment="联系方式")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    province = Column(String(50), comment="所在省份")
    city = Column(String(50), comment="所在城市")
    source_channel = Column(String(100), comment="来源渠道/分销")
    tags = Column(String(500), comment="标签")
    remarks = Column(Text, comment="备注")
    
    # 派生数据
    total_consume_count = Column(Integer, default=0, comment="累计消费次数")
    total_consume_amount = Column(Numeric(10, 2), default=0, comment="累计消费金额")
    activation_time = Column(DateTime(timezone=True), comment="激活时间")
    first_consume_time = Column(DateTime(timezone=True), comment="首次消费时间")


class SyncTaskLogModel(Base):
    """同步任务日志表"""
    __tablename__ = "sync_task_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column(String(100), nullable=False, comment="任务名称")
    task_type = Column(String(50), nullable=False, comment="任务类型")
    start_time = Column(DateTime(timezone=True), nullable=False, comment="开始时间")
    end_time = Column(DateTime(timezone=True), comment="结束时间")
    status = Column(String(20), nullable=False, comment="执行状态")
    success_count = Column(Integer, default=0, comment="成功数量")
    error_count = Column(Integer, default=0, comment="失败数量")
    error_message = Column(Text, comment="错误信息")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")


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