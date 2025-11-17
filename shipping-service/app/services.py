"""
发货服务业务逻辑
处理发货相关的核心业务逻辑 - 支持门票二维码生成和第三方发货
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import httpx
import asyncio
import random
import string
import qrcode
import io
import base64
import json
import uuid
import sys
import os

from .models import (
    Shipping, ShippingCreate, ShippingStatus, 
    UserAsset, AssetType, AssetStatus,
    OrderItem
)
# 添加共享模块到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))
from .config import ShippingServiceConfig
from .utils import generate_shipping_id, setup_logging

from .database import ShippingModel, UserAssetModel

# 初始化配置和日志
config = ShippingServiceConfig()
logger = setup_logging("shipping-service")


class QRCodeService:
    """二维码生成服务"""
    
    def __init__(self):
        self.base_url = os.getenv("QR_CODE_BASE_URL", "https://qr.example.com")
    
    def generate_ticket_qr_code(self, ticket_data: Dict[str, Any]) -> Dict[str, str]:
        """生成门票二维码"""
        try:
            # 构造二维码内容
            qr_content = {
                "type": "ticket",
                "ticket_id": ticket_data["ticket_id"],
                "user_id": ticket_data["user_id"],
                "scenic_area_id": ticket_data["scenic_area_id"],
                "valid_from": ticket_data["valid_from"],
                "valid_until": ticket_data["valid_until"],
                "timestamp": datetime.now().isoformat()
            }
            
            # 转换为JSON字符串
            qr_content_str = json.dumps(qr_content, ensure_ascii=False)
            
            # 生成二维码图片
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_content_str)
            qr.make(fit=True)
            
            # 创建二维码图片
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 转换为base64
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            
            # 模拟上传到文件服务器（实际环境中替换为真实的文件上传服务）
            qr_image_url = f"{self.base_url}/qr/{ticket_data['ticket_id']}.png"
            
            logger.info(f"门票二维码生成成功: {ticket_data['ticket_id']}")
            
            return {
                "qr_content": qr_content_str,
                "qr_image_url": qr_image_url,
                "qr_base64": img_base64
            }
            
        except Exception as e:
            logger.error(f"生成门票二维码失败: {str(e)}")
            raise


class ThirdPartyShippingAPI:
    """第三方发货系统API接口"""
    
    def __init__(self):
        self.base_url = "https://api.shipping-provider.com"
        self.api_key = os.getenv("SHIPPING_API_KEY", "test_api_key")
        self.timeout = 30.0
    
    async def create_shipping_order(self, shipping_data: Dict[str, Any]) -> Dict[str, Any]:
        """调用第三方系统创建发货订单（仅用于实物商品）"""
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "order_id": shipping_data["order_id"],
                    "recipient": {
                        "name": shipping_data.get("recipient_name", ""),
                        "phone": shipping_data["phone"],
                        "address": shipping_data["shipping_address"]
                    },
                    "items": shipping_data.get("items", []),
                    "service_type": shipping_data.get("service_type", "standard"),
                    "notes": shipping_data.get("notes", "")
                }
                
                # 模拟调用第三方API
                response = await self._mock_api_call(payload)
                
                if response["success"]:
                    return {
                        "success": True,
                        "shipping_order_id": response["data"]["shipping_order_id"],
                        "tracking_number": response["data"]["tracking_number"],
                        "carrier": response["data"]["carrier"],
                        "estimated_delivery": response["data"]["estimated_delivery"]
                    }
                else:
                    return {
                        "success": False,
                        "error": response["error"]
                    }
                    
        except Exception as e:
            logger.error(f"调用第三方发货API失败: {str(e)}")
            return {
                "success": False,
                "error": f"第三方系统调用失败: {str(e)}"
            }
    
    async def cancel_shipping_order(self, shipping_order_id: str) -> Dict[str, Any]:
        """取消第三方发货订单"""
        try:
            await asyncio.sleep(1)
            return {
                "success": True,
                "message": "发货订单已取消"
            }
        except Exception as e:
            logger.error(f"取消第三方发货订单失败: {str(e)}")
            return {
                "success": False,
                "error": f"取消发货失败: {str(e)}"
            }
    
    async def query_shipping_status(self, tracking_number: str) -> Dict[str, Any]:
        """查询第三方发货状态"""
        try:
            await asyncio.sleep(0.5)
            statuses = ["preparing", "shipped", "in_transit", "delivered"]
            current_status = random.choice(statuses)
            
            return {
                "success": True,
                "tracking_number": tracking_number,
                "status": current_status,
                "last_update": datetime.now().isoformat(),
                "location": "北京分拣中心" if current_status == "in_transit" else None
            }
        except Exception as e:
            logger.error(f"查询第三方发货状态失败: {str(e)}")
            return {
                "success": False,
                "error": f"查询发货状态失败: {str(e)}"
            }
    
    async def _mock_api_call(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """模拟第三方API调用"""
        await asyncio.sleep(1)
        return {
            "success": True,
            "data": {
                "shipping_order_id": f"SHP_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}",
                "tracking_number": f"SF{datetime.now().strftime('%Y%m%d')}{random.randint(10000000, 99999999)}",
                "carrier": "顺丰速运",
                "estimated_delivery": (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).isoformat()
            }
        }


class UserAssetService:
    """用户资产服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.qr_service = QRCodeService()
    
    async def create_ticket_asset(self, user_id: str, order_item: OrderItem, order_id: str) -> UserAsset:
        """创建门票资产"""
        try:
            # 生成资产ID
            asset_id = f"TICKET_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
            
            # 计算有效期
            valid_from = datetime.now()
            valid_until = valid_from + timedelta(days=order_item.valid_days or 365)
            
            # 准备门票数据
            ticket_data = {
                "ticket_id": asset_id,
                "user_id": user_id,
                "scenic_area_id": order_item.scenic_area_id,
                "scenic_area_name": order_item.scenic_area_name,
                "ticket_type": order_item.ticket_type,
                "valid_from": valid_from.isoformat(),
                "valid_until": valid_until.isoformat()
            }
            
            # 生成二维码
            qr_result = self.qr_service.generate_ticket_qr_code(ticket_data)
            
            # 准备资产元数据
            metadata = {
                "scenic_area_id": order_item.scenic_area_id,
                "scenic_area_name": order_item.scenic_area_name,
                "ticket_type": order_item.ticket_type,
                "unit_price": float(order_item.unit_price),
                "qr_base64": qr_result["qr_base64"]
            }
            
            # 创建资产记录
            db_asset = UserAssetModel(
                id=asset_id,
                user_id=user_id,
                asset_type=AssetType.TICKET.value,
                asset_name=f"{order_item.scenic_area_name} - {order_item.ticket_type}",
                asset_code=qr_result["qr_content"],
                qr_code_url=qr_result["qr_image_url"],
                order_id=order_id,
                status=AssetStatus.ACTIVE.value,
                metadata=metadata,
                valid_from=valid_from,
                valid_until=valid_until
            )
            
            self.db.add(db_asset)
            await self.db.commit()
            await self.db.refresh(db_asset)
            
            logger.info(f"门票资产创建成功: {asset_id}")
            return self._db_to_model(db_asset)
            
        except Exception as e:
            logger.error(f"创建门票资产失败: {str(e)}")
            await self.db.rollback()
            raise
    
    async def get_user_assets(self, user_id: str, asset_type: Optional[AssetType] = None) -> List[UserAsset]:
        """获取用户资产列表"""
        try:
            query = select(UserAssetModel).where(UserAssetModel.user_id == user_id)
            
            if asset_type:
                query = query.where(UserAssetModel.asset_type == asset_type.value)
            
            result = await self.db.execute(query.order_by(UserAssetModel.created_at.desc()))
            db_assets = result.scalars().all()
            
            return [self._db_to_model(asset) for asset in db_assets]
            
        except Exception as e:
            logger.error(f"获取用户资产失败: {str(e)}")
            raise
    
    async def get_asset_by_code(self, asset_code: str) -> Optional[UserAsset]:
        """根据资产编码获取资产"""
        try:
            result = await self.db.execute(
                select(UserAssetModel).where(UserAssetModel.asset_code == asset_code)
            )
            db_asset = result.scalar_one_or_none()
            
            if db_asset:
                return self._db_to_model(db_asset)
            return None
            
        except Exception as e:
            logger.error(f"根据编码获取资产失败: {str(e)}")
            raise
    
    async def use_asset(self, asset_id: str) -> bool:
        """使用资产"""
        try:
            result = await self.db.execute(
                update(UserAssetModel)
                .where(UserAssetModel.id == asset_id)
                .where(UserAssetModel.status == AssetStatus.ACTIVE.value)
                .values(
                    status=AssetStatus.USED.value,
                    used_at=datetime.now()
                )
            )
            
            if result.rowcount > 0:
                await self.db.commit()
                logger.info(f"资产使用成功: {asset_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"使用资产失败: {str(e)}")
            await self.db.rollback()
            raise
    
    def _db_to_model(self, db_asset: UserAssetModel) -> UserAsset:
        """将数据库模型转换为业务模型"""
        return UserAsset(
            id=db_asset.id,
            user_id=db_asset.user_id,
            asset_type=AssetType(db_asset.asset_type),
            asset_name=db_asset.asset_name,
            asset_code=db_asset.asset_code,
            qr_code_url=db_asset.qr_code_url,
            order_id=db_asset.order_id,
            status=AssetStatus(db_asset.status),
            metadata=db_asset.metadata,
            valid_from=db_asset.valid_from,
            valid_until=db_asset.valid_until,
            used_at=db_asset.used_at,
            created_at=db_asset.created_at,
            updated_at=db_asset.updated_at
        )


class ShippingService:
    """发货服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.third_party_api = ThirdPartyShippingAPI()
        self.asset_service = UserAssetService(db)
    
    async def create_shipping(self, shipping_data: ShippingCreate, order_items: List[OrderItem] = None) -> Shipping:
        """创建发货记录"""
        try:
            shipping_id = generate_shipping_id()
            
            db_shipping = ShippingModel(
                id=shipping_id,
                order_id=shipping_data.order_id,
                shipping_address=shipping_data.shipping_address,
                phone=shipping_data.phone,
                status=ShippingStatus.PENDING.value
            )
            
            self.db.add(db_shipping)
            await self.db.commit()
            await self.db.refresh(db_shipping)
            
            shipping = self._db_to_model(db_shipping)
            logger.info(f"发货记录创建成功: {shipping_id}")
            
            return shipping
            
        except Exception as e:
            logger.error(f"创建发货记录失败: {str(e)}")
            await self.db.rollback()
            raise
    
    async def process_shipping(self, shipping_id: str, order_items: List[OrderItem] = None, user_id: str = None) -> bool:
        """处理发货 - 根据商品类型选择处理方式"""
        try:
            shipping = await self.get_shipping(shipping_id)
            if not shipping:
                raise ValueError("发货记录不存在")
            
            if shipping.status != ShippingStatus.PENDING:
                raise ValueError("发货状态不正确，无法处理")
            
            await self.update_shipping_status(shipping_id, ShippingStatus.PREPARING)
            
            # 分类处理订单商品
            ticket_items = []
            physical_items = []
            
            for item in order_items or []:
                if item.product_type == "ticket":
                    ticket_items.append(item)
                else:
                    physical_items.append(item)
            
            # 处理门票商品 - 生成二维码和用户资产
            if ticket_items and user_id:
                await self._process_ticket_items(ticket_items, user_id, shipping.order_id)
            
            # 处理实物商品 - 调用第三方发货系统
            if physical_items:
                await self._process_physical_items(shipping, physical_items)
            
            # 如果只有门票，直接标记为已发货
            if ticket_items and not physical_items:
                await self.update_shipping_status(shipping_id, ShippingStatus.SHIPPED)
                await self._notify_order_service(shipping.order_id, "shipped")
            
            logger.info(f"发货处理成功: {shipping_id}")
            return True
            
        except Exception as e:
            logger.error(f"处理发货失败: {str(e)}")
            await self.update_shipping_status(shipping_id, ShippingStatus.PENDING)
            raise
    
    async def _process_ticket_items(self, ticket_items: List[OrderItem], user_id: str, order_id: str):
        """处理门票商品"""
        try:
            for item in ticket_items:
                # 为每个门票数量创建对应的资产
                for _ in range(item.quantity):
                    await self.asset_service.create_ticket_asset(user_id, item, order_id)
            
            logger.info(f"门票处理完成，共创建 {sum(item.quantity for item in ticket_items)} 张门票")
            
        except Exception as e:
            logger.error(f"处理门票商品失败: {str(e)}")
            raise
    
    async def _process_physical_items(self, shipping: Shipping, physical_items: List[OrderItem]):
        """处理实物商品"""
        try:
            shipping_request_data = {
                "order_id": shipping.order_id,
                "shipping_address": shipping.shipping_address,
                "phone": shipping.phone,
                "items": [item.dict() for item in physical_items],
                "service_type": "standard",
                "notes": "系统自动发货"
            }
            
            result = await self.third_party_api.create_shipping_order(shipping_request_data)
            
            if result["success"]:
                await self.update_shipping_status(
                    shipping.id,
                    ShippingStatus.SHIPPED,
                    result["tracking_number"],
                    result["carrier"]
                )
                await self._notify_order_service(shipping.order_id, "shipped")
                logger.info(f"实物商品发货成功: {shipping.id}")
            else:
                raise Exception(f"第三方发货失败: {result['error']}")
                
        except Exception as e:
            logger.error(f"处理实物商品失败: {str(e)}")
            raise
    
    async def get_shipping(self, shipping_id: str) -> Optional[Shipping]:
        """根据ID获取发货记录"""
        try:
            result = await self.db.execute(
                select(ShippingModel).where(ShippingModel.id == shipping_id)
            )
            db_shipping = result.scalar_one_or_none()
            
            if db_shipping:
                return self._db_to_model(db_shipping)
            return None
            
        except Exception as e:
            logger.error(f"获取发货记录失败: {str(e)}")
            raise
    
    async def get_shipping_by_order(self, order_id: str) -> Optional[Shipping]:
        """根据订单ID获取发货记录"""
        try:
            result = await self.db.execute(
                select(ShippingModel).where(ShippingModel.order_id == order_id)
            )
            db_shipping = result.scalar_one_or_none()
            
            if db_shipping:
                return self._db_to_model(db_shipping)
            return None
            
        except Exception as e:
            logger.error(f"根据订单获取发货记录失败: {str(e)}")
            raise
    
    async def update_shipping_status(
        self, 
        shipping_id: str, 
        status: ShippingStatus,
        tracking_number: Optional[str] = None,
        carrier: Optional[str] = None
    ) -> bool:
        """更新发货状态"""
        try:
            update_data = {"status": status.value}
            
            if status == ShippingStatus.SHIPPED:
                update_data["shipped_at"] = datetime.now()
            elif status == ShippingStatus.DELIVERED:
                update_data["delivered_at"] = datetime.now()
            
            if tracking_number:
                update_data["tracking_number"] = tracking_number
            if carrier:
                update_data["carrier"] = carrier
            
            result = await self.db.execute(
                update(ShippingModel)
                .where(ShippingModel.id == shipping_id)
                .values(**update_data)
            )
            
            if result.rowcount > 0:
                await self.db.commit()
                logger.info(f"发货状态更新成功: {shipping_id} -> {status.value}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"更新发货状态失败: {str(e)}")
            await self.db.rollback()
            raise
    
    async def cancel_shipping(self, shipping_id: str) -> bool:
        """取消发货"""
        try:
            shipping = await self.get_shipping(shipping_id)
            if not shipping:
                raise ValueError("发货记录不存在")
            
            if shipping.status in [ShippingStatus.DELIVERED]:
                raise ValueError("已送达的发货无法取消")
            
            if shipping.tracking_number and shipping.status in [ShippingStatus.SHIPPED, ShippingStatus.IN_TRANSIT]:
                cancel_result = await self.third_party_api.cancel_shipping_order(shipping.tracking_number)
                if not cancel_result["success"]:
                    logger.warning(f"取消第三方发货订单失败: {cancel_result['error']}")
            
            await self.update_shipping_status(shipping_id, ShippingStatus.CANCELLED)
            await self._notify_order_service(shipping.order_id, "shipping_cancelled")
            
            logger.info(f"发货取消成功: {shipping_id}")
            return True
            
        except Exception as e:
            logger.error(f"取消发货失败: {str(e)}")
            raise
    
    def _db_to_model(self, db_shipping: ShippingModel) -> Shipping:
        """将数据库模型转换为业务模型"""
        return Shipping(
            id=db_shipping.id,
            order_id=db_shipping.order_id,
            tracking_number=db_shipping.tracking_number,
            carrier=db_shipping.carrier,
            shipping_address=db_shipping.shipping_address,
            phone=db_shipping.phone,
            status=ShippingStatus(db_shipping.status),
            shipped_at=db_shipping.shipped_at,
            delivered_at=db_shipping.delivered_at,
            created_at=db_shipping.created_at,
            updated_at=db_shipping.updated_at
        )
    
    async def _notify_order_service(self, order_id: str, status: str):
        """通知订单服务"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{config.order_service_url}/api/v1/orders/{order_id}/status",
                    json={"status": status},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"订单状态通知成功: {order_id} -> {status}")
                else:
                    logger.error(f"订单状态通知失败: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"通知订单服务失败: {str(e)}")