"""
订单服务数据模型
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from decimal import Decimal


class OrderStatus(str, Enum):
    """订单状态枚举"""
    PENDING = "pending"          # 待处理
    CONFIRMED = "confirmed"      # 已确认
    PAID = "paid"               # 已支付
    SHIPPED = "shipped"         # 已发货
    DELIVERED = "delivered"     # 已送达
    CANCELLED = "cancelled"     # 已取消
    REFUNDED = "refunded"       # 已退款


class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None


class OrderItem(BaseModel):
    """订单商品项"""
    product_id: str = Field(..., description="商品ID")
    product_name: str = Field(..., description="商品名称")
    product_type: str = Field(default="ticket", description="商品类型：ticket/physical")
    quantity: int = Field(..., gt=0, description="数量")
    unit_price: Decimal = Field(..., gt=0, description="单价")
    total_price: Decimal = Field(..., description="小计")
    # 门票相关字段
    scenic_area_id: Optional[str] = Field(None, description="景区ID")
    scenic_area_name: Optional[str] = Field(None, description="景区名称")
    valid_days: Optional[int] = Field(None, description="有效天数")
    ticket_type: Optional[str] = Field(None, description="门票类型")


class OrderCreate(BaseModel):
    """创建订单请求"""
    user_id: str = Field(..., description="用户ID")
    items: List[OrderItem] = Field(..., description="订单商品列表")
    shipping_address: str = Field(..., description="收货地址")
    phone: str = Field(..., description="联系电话")
    notes: Optional[str] = Field(None, description="订单备注")


class Order(BaseModel):
    """订单模型"""
    id: str = Field(..., description="订单ID")
    user_id: str = Field(..., description="用户ID")
    items: List[OrderItem] = Field(..., description="订单商品列表")
    total_amount: Decimal = Field(..., description="订单总金额")
    status: OrderStatus = Field(default=OrderStatus.PENDING, description="订单状态")
    shipping_address: str = Field(..., description="收货地址")
    phone: str = Field(..., description="联系电话")
    notes: Optional[str] = Field(None, description="订单备注")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")