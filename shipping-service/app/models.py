"""
发货服务数据模型
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from decimal import Decimal


class ShippingStatus(str, Enum):
    """发货状态枚举"""
    PENDING = "pending"         # 待发货
    PREPARING = "preparing"     # 准备中（生成二维码中）
    SHIPPED = "shipped"         # 已发货（二维码已生成）
    IN_TRANSIT = "in_transit"   # 运输中（物理商品）
    DELIVERED = "delivered"     # 已送达
    CANCELLED = "cancelled"     # 已取消
    RETURNED = "returned"       # 已退回


class AssetType(str, Enum):
    """资产类型枚举"""
    TICKET = "ticket"           # 门票
    VOUCHER = "voucher"         # 代金券
    MEMBERSHIP = "membership"   # 会员卡
    POINTS = "points"           # 积分
    PHYSICAL = "physical"       # 实物商品


class AssetStatus(str, Enum):
    """资产状态枚举"""
    ACTIVE = "active"           # 有效
    USED = "used"              # 已使用
    EXPIRED = "expired"        # 已过期
    CANCELLED = "cancelled"    # 已取消
    FROZEN = "frozen"          # 已冻结


class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None


class OrderItem(BaseModel):
    """订单商品项（用于发货处理）"""
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


class ShippingCreate(BaseModel):
    """创建发货请求"""
    order_id: str = Field(..., description="订单ID")
    shipping_address: str = Field(..., description="收货地址")
    phone: str = Field(..., description="联系电话")
    recipient_name: Optional[str] = Field(None, description="收货人姓名")
    service_type: Optional[str] = Field("standard", description="发货服务类型")
    notes: Optional[str] = Field(None, description="发货备注")


class Shipping(BaseModel):
    """发货模型"""
    id: str = Field(..., description="发货ID")
    order_id: str = Field(..., description="订单ID")
    tracking_number: Optional[str] = Field(None, description="快递单号")
    carrier: Optional[str] = Field(None, description="承运商")
    shipping_address: str = Field(..., description="收货地址")
    phone: str = Field(..., description="联系电话")
    status: ShippingStatus = Field(default=ShippingStatus.PENDING, description="发货状态")
    shipped_at: Optional[datetime] = Field(None, description="发货时间")
    delivered_at: Optional[datetime] = Field(None, description="送达时间")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


class UserAssetCreate(BaseModel):
    """创建用户资产请求"""
    user_id: str = Field(..., description="用户ID")
    asset_type: AssetType = Field(..., description="资产类型")
    asset_name: str = Field(..., description="资产名称")
    asset_code: str = Field(..., description="资产编码/二维码内容")
    order_id: Optional[str] = Field(None, description="关联订单ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="资产元数据")
    valid_from: Optional[datetime] = Field(None, description="有效期开始")
    valid_until: Optional[datetime] = Field(None, description="有效期结束")


class UserAsset(BaseModel):
    """用户资产模型"""
    id: str = Field(..., description="资产ID")
    user_id: str = Field(..., description="用户ID")
    asset_type: AssetType = Field(..., description="资产类型")
    asset_name: str = Field(..., description="资产名称")
    asset_code: str = Field(..., description="资产编码/二维码内容")
    qr_code_url: Optional[str] = Field(None, description="二维码图片URL")
    order_id: Optional[str] = Field(None, description="关联订单ID")
    status: AssetStatus = Field(default=AssetStatus.ACTIVE, description="资产状态")
    metadata: Optional[Dict[str, Any]] = Field(None, description="资产元数据")
    valid_from: Optional[datetime] = Field(None, description="有效期开始")
    valid_until: Optional[datetime] = Field(None, description="有效期结束")
    used_at: Optional[datetime] = Field(None, description="使用时间")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


class TicketQRCode(BaseModel):
    """门票二维码模型"""
    ticket_id: str = Field(..., description="门票ID")
    qr_content: str = Field(..., description="二维码内容")
    qr_image_url: str = Field(..., description="二维码图片URL")
    scenic_area_id: str = Field(..., description="景区ID")
    scenic_area_name: str = Field(..., description="景区名称")
    ticket_type: str = Field(..., description="门票类型")
    valid_from: datetime = Field(..., description="有效期开始")
    valid_until: datetime = Field(..., description="有效期结束")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")


class ThirdPartyShippingRequest(BaseModel):
    """第三方发货系统请求模型"""
    order_id: str = Field(..., description="订单ID")
    recipient_name: str = Field(..., description="收货人姓名")
    phone: str = Field(..., description="联系电话")
    address: str = Field(..., description="收货地址")
    items: List[Dict[str, Any]] = Field(..., description="商品列表")
    service_type: str = Field(default="standard", description="服务类型")
    notes: Optional[str] = Field(None, description="备注")


class ThirdPartyShippingResponse(BaseModel):
    """第三方发货系统响应模型"""
    success: bool = Field(..., description="是否成功")
    shipping_order_id: Optional[str] = Field(None, description="第三方发货订单ID")
    tracking_number: Optional[str] = Field(None, description="快递单号")
    carrier: Optional[str] = Field(None, description="承运商")
    estimated_delivery: Optional[str] = Field(None, description="预计送达时间")
    error: Optional[str] = Field(None, description="错误信息")