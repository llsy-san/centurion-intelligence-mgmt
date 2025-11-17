"""
订单服务业务逻辑
处理订单相关的核心业务逻辑
"""
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional

from .models import Order, OrderCreate, OrderStatus, OrderItem
from .config import OrderServiceConfig
from .utils import generate_order_number, setup_logging
from .database import OrderModel

# 初始化配置和日志
config = OrderServiceConfig()
logger = setup_logging("order-service")


class OrderService:
    """订单服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_order(self, order_data: OrderCreate) -> Order:
        """创建订单"""
        try:
            # 生成订单ID
            order_id = generate_order_number()
            
            # 计算订单总金额
            total_amount = sum(item.total_price for item in order_data.items)
            
            # 创建订单模型
            db_order = OrderModel(
                id=order_id,
                user_id=order_data.user_id,
                items=[item.dict() for item in order_data.items],
                total_amount=total_amount,
                status=OrderStatus.PENDING.value,
                shipping_address=order_data.shipping_address,
                phone=order_data.phone,
                notes=order_data.notes
            )
            
            # 保存到数据库
            self.db.add(db_order)
            await self.db.commit()
            await self.db.refresh(db_order)
            
            # 转换为业务模型
            order = self._db_to_model(db_order)
            
            logger.info(f"订单创建成功: {order_id}")
            
            # 发送订单创建事件（这里可以集成消息队列）
            await self._publish_order_created_event(order)
            
            return order
            
        except Exception as e:
            logger.error(f"创建订单失败: {str(e)}")
            await self.db.rollback()
            raise
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        """根据ID获取订单"""
        try:
            result = await self.db.execute(
                select(OrderModel).where(OrderModel.id == order_id)
            )
            db_order = result.scalar_one_or_none()
            
            if db_order:
                return self._db_to_model(db_order)
            return None
            
        except Exception as e:
            logger.error(f"获取订单失败: {str(e)}")
            raise
    
    async def get_orders_by_user(self, user_id: str, skip: int = 0, limit: int = 10) -> List[Order]:
        """根据用户ID获取订单列表"""
        try:
            result = await self.db.execute(
                select(OrderModel)
                .where(OrderModel.user_id == user_id)
                .order_by(OrderModel.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            db_orders = result.scalars().all()
            
            return [self._db_to_model(db_order) for db_order in db_orders]
            
        except Exception as e:
            logger.error(f"获取用户订单列表失败: {str(e)}")
            raise
    
    async def update_order_status(self, order_id: str, status: OrderStatus) -> bool:
        """更新订单状态"""
        try:
            result = await self.db.execute(
                update(OrderModel)
                .where(OrderModel.id == order_id)
                .values(status=status.value)
            )
            
            if result.rowcount > 0:
                await self.db.commit()
                logger.info(f"订单状态更新成功: {order_id} -> {status.value}")
                
                # 发送订单状态更新事件
                await self._publish_order_status_updated_event(order_id, status)
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"更新订单状态失败: {str(e)}")
            await self.db.rollback()
            raise
    
    async def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        try:
            # 检查订单状态是否可以取消
            order = await self.get_order(order_id)
            if not order:
                return False
            
            if order.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
                raise ValueError("已发货或已送达的订单无法取消")
            
            # 更新订单状态为已取消
            return await self.update_order_status(order_id, OrderStatus.CANCELLED)
            
        except Exception as e:
            logger.error(f"取消订单失败: {str(e)}")
            raise
    
    def _db_to_model(self, db_order: OrderModel) -> Order:
        """将数据库模型转换为业务模型"""
        items = [OrderItem(**item) for item in db_order.items]
        
        return Order(
            id=db_order.id,
            user_id=db_order.user_id,
            items=items,
            total_amount=db_order.total_amount,
            status=OrderStatus(db_order.status),
            shipping_address=db_order.shipping_address,
            phone=db_order.phone,
            notes=db_order.notes,
            created_at=db_order.created_at,
            updated_at=db_order.updated_at
        )
    
    async def _publish_order_created_event(self, order: Order):
        """发布订单创建事件"""
        # 这里可以集成RabbitMQ或其他消息队列
        # 暂时使用HTTP通知其他服务
        try:
            event_data = {
                "event_type": "order_created",
                "order_id": order.id,
                "user_id": order.user_id,
                "total_amount": float(order.total_amount),
                "timestamp": order.created_at.isoformat()
            }
            logger.info(f"发布订单创建事件: {event_data}")
            
        except Exception as e:
            logger.error(f"发布订单创建事件失败: {str(e)}")
    
    async def _publish_order_status_updated_event(self, order_id: str, status: OrderStatus):
        """发布订单状态更新事件"""
        try:
            event_data = {
                "event_type": "order_status_updated",
                "order_id": order_id,
                "status": status.value,
                "timestamp": datetime.now().isoformat()
            }
            logger.info(f"发布订单状态更新事件: {event_data}")
            
        except Exception as e:
            logger.error(f"发布订单状态更新事件失败: {str(e)}")