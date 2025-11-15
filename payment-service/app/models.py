"""
支付服务数据模型
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from decimal import Decimal


class PaymentStatus(str, Enum):
    """支付状态枚举"""
    PENDING = "pending"         # 待支付
    PROCESSING = "processing"   # 处理中
    SUCCESS = "success"         # 支付成功
    FAILED = "failed"          # 支付失败
    REFUNDED = "refunded"      # 已退款


class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None


class PaymentCreate(BaseModel):
    """创建支付请求"""
    order_id: str = Field(..., description="订单ID")
    amount: Decimal = Field(..., gt=0, description="支付金额")
    payment_method: str = Field(..., description="支付方式")


class Payment(BaseModel):
    """支付模型"""
    id: str = Field(..., description="支付ID")
    order_id: str = Field(..., description="订单ID")
    amount: Decimal = Field(..., description="支付金额")
    payment_method: str = Field(..., description="支付方式")
    status: PaymentStatus = Field(default=PaymentStatus.PENDING, description="支付状态")
    transaction_id: Optional[str] = Field(None, description="第三方交易ID")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")