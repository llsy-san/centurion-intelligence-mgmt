"""
AI智能代理服务数据模型
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


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