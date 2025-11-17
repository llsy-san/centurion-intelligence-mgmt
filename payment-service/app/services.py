"""
支付服务业务逻辑
处理支付相关的核心业务逻辑
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional, Dict, Any
import httpx
import asyncio

from .models import Payment, PaymentCreate, PaymentStatus
from .config import PaymentServiceConfig
from .utils import generate_payment_id, setup_logging, calculate_signature

from .database import PaymentModel

# 初始化配置和日志
config = PaymentServiceConfig()
logger = setup_logging("payment-service")


class PaymentService:
    """支付服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_payment(self, payment_data: PaymentCreate) -> Payment:
        """创建支付"""
        try:
            # 生成支付ID
            payment_id = generate_payment_id()
            
            # 创建支付模型
            db_payment = PaymentModel(
                id=payment_id,
                order_id=payment_data.order_id,
                amount=payment_data.amount,
                payment_method=payment_data.payment_method,
                status=PaymentStatus.PENDING.value
            )
            
            # 保存到数据库
            self.db.add(db_payment)
            await self.db.commit()
            await self.db.refresh(db_payment)
            
            # 转换为业务模型
            payment = self._db_to_model(db_payment)
            
            logger.info(f"支付创建成功: {payment_id}")
            
            return payment
            
        except Exception as e:
            logger.error(f"创建支付失败: {str(e)}")
            await self.db.rollback()
            raise
    
    async def process_payment(self, payment_id: str) -> bool:
        """处理支付"""
        try:
            # 获取支付信息
            payment = await self.get_payment(payment_id)
            if not payment:
                raise ValueError("支付记录不存在")
            
            if payment.status != PaymentStatus.PENDING:
                raise ValueError("支付状态不正确")
            
            # 更新支付状态为处理中
            await self.update_payment_status(payment_id, PaymentStatus.PROCESSING)
            
            # 根据支付方式调用相应的支付接口
            success = False
            transaction_id = None
            
            if payment.payment_method == "alipay":
                success, transaction_id = await self._process_alipay_payment(payment)
            elif payment.payment_method == "wechat":
                success, transaction_id = await self._process_wechat_payment(payment)
            elif payment.payment_method == "mock":
                # 模拟支付，用于测试
                success, transaction_id = await self._process_mock_payment(payment)
            else:
                raise ValueError(f"不支持的支付方式: {payment.payment_method}")
            
            # 更新支付状态和交易ID
            if success:
                await self.update_payment_status(
                    payment_id, 
                    PaymentStatus.SUCCESS, 
                    transaction_id
                )
                
                # 通知订单服务支付成功
                await self._notify_order_service(payment.order_id, "paid")
                
                logger.info(f"支付处理成功: {payment_id}")
            else:
                await self.update_payment_status(payment_id, PaymentStatus.FAILED)
                logger.error(f"支付处理失败: {payment_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"处理支付失败: {str(e)}")
            await self.update_payment_status(payment_id, PaymentStatus.FAILED)
            raise
    
    async def get_payment(self, payment_id: str) -> Optional[Payment]:
        """根据ID获取支付"""
        try:
            result = await self.db.execute(
                select(PaymentModel).where(PaymentModel.id == payment_id)
            )
            db_payment = result.scalar_one_or_none()
            
            if db_payment:
                return self._db_to_model(db_payment)
            return None
            
        except Exception as e:
            logger.error(f"获取支付失败: {str(e)}")
            raise
    
    async def get_payment_by_order(self, order_id: str) -> Optional[Payment]:
        """根据订单ID获取支付"""
        try:
            result = await self.db.execute(
                select(PaymentModel).where(PaymentModel.order_id == order_id)
            )
            db_payment = result.scalar_one_or_none()
            
            if db_payment:
                return self._db_to_model(db_payment)
            return None
            
        except Exception as e:
            logger.error(f"根据订单获取支付失败: {str(e)}")
            raise
    
    async def update_payment_status(
        self, 
        payment_id: str, 
        status: PaymentStatus, 
        transaction_id: Optional[str] = None
    ) -> bool:
        """更新支付状态"""
        try:
            update_data = {"status": status.value}
            if transaction_id:
                update_data["transaction_id"] = transaction_id
            
            result = await self.db.execute(
                update(PaymentModel)
                .where(PaymentModel.id == payment_id)
                .values(**update_data)
            )
            
            if result.rowcount > 0:
                await self.db.commit()
                logger.info(f"支付状态更新成功: {payment_id} -> {status.value}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"更新支付状态失败: {str(e)}")
            await self.db.rollback()
            raise
    
    async def refund_payment(self, payment_id: str) -> bool:
        """退款"""
        try:
            payment = await self.get_payment(payment_id)
            if not payment:
                raise ValueError("支付记录不存在")
            
            if payment.status != PaymentStatus.SUCCESS:
                raise ValueError("只有成功的支付才能退款")
            
            # 调用第三方退款接口
            refund_success = False
            
            if payment.payment_method == "alipay":
                refund_success = await self._process_alipay_refund(payment)
            elif payment.payment_method == "wechat":
                refund_success = await self._process_wechat_refund(payment)
            elif payment.payment_method == "mock":
                refund_success = True  # 模拟退款成功
            
            if refund_success:
                await self.update_payment_status(payment_id, PaymentStatus.REFUNDED)
                
                # 通知订单服务退款成功
                await self._notify_order_service(payment.order_id, "refunded")
                
                logger.info(f"退款成功: {payment_id}")
            
            return refund_success
            
        except Exception as e:
            logger.error(f"退款失败: {str(e)}")
            raise
    
    def _db_to_model(self, db_payment: PaymentModel) -> Payment:
        """将数据库模型转换为业务模型"""
        return Payment(
            id=db_payment.id,
            order_id=db_payment.order_id,
            amount=db_payment.amount,
            payment_method=db_payment.payment_method,
            status=PaymentStatus(db_payment.status),
            transaction_id=db_payment.transaction_id,
            created_at=db_payment.created_at,
            updated_at=db_payment.updated_at
        )
    
    async def _process_alipay_payment(self, payment: Payment) -> tuple[bool, Optional[str]]:
        """处理支付宝支付"""
        try:
            # 这里应该调用支付宝SDK
            # 暂时模拟支付成功
            await asyncio.sleep(1)  # 模拟网络延迟
            
            # 模拟生成交易ID
            transaction_id = f"alipay_{payment.id}_{int(payment.created_at.timestamp())}"
            
            logger.info(f"支付宝支付处理: {payment.id}")
            return True, transaction_id
            
        except Exception as e:
            logger.error(f"支付宝支付失败: {str(e)}")
            return False, None
    
    async def _process_wechat_payment(self, payment: Payment) -> tuple[bool, Optional[str]]:
        """处理微信支付"""
        try:
            # 这里应该调用微信支付SDK
            # 暂时模拟支付成功
            await asyncio.sleep(1)  # 模拟网络延迟
            
            # 模拟生成交易ID
            transaction_id = f"wechat_{payment.id}_{int(payment.created_at.timestamp())}"
            
            logger.info(f"微信支付处理: {payment.id}")
            return True, transaction_id
            
        except Exception as e:
            logger.error(f"微信支付失败: {str(e)}")
            return False, None
    
    async def _process_mock_payment(self, payment: Payment) -> tuple[bool, Optional[str]]:
        """处理模拟支付"""
        try:
            # 模拟支付处理
            await asyncio.sleep(0.5)
            
            # 模拟生成交易ID
            transaction_id = f"mock_{payment.id}_{int(payment.created_at.timestamp())}"
            
            logger.info(f"模拟支付处理: {payment.id}")
            return True, transaction_id
            
        except Exception as e:
            logger.error(f"模拟支付失败: {str(e)}")
            return False, None
    
    async def _process_alipay_refund(self, payment: Payment) -> bool:
        """处理支付宝退款"""
        try:
            # 这里应该调用支付宝退款SDK
            await asyncio.sleep(1)
            logger.info(f"支付宝退款处理: {payment.id}")
            return True
            
        except Exception as e:
            logger.error(f"支付宝退款失败: {str(e)}")
            return False
    
    async def _process_wechat_refund(self, payment: Payment) -> bool:
        """处理微信退款"""
        try:
            # 这里应该调用微信退款SDK
            await asyncio.sleep(1)
            logger.info(f"微信退款处理: {payment.id}")
            return True
            
        except Exception as e:
            logger.error(f"微信退款失败: {str(e)}")
            return False
    
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