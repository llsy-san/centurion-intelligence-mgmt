"""
同步服务
处理第三方数据同步逻辑
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../shared'))
from utils import setup_logging

from ..database import (
    OrderSyncModel, OrderProductSyncModel, ProductModel, 
    OrganizationModel, SyncTaskLogModel, get_db
)
from .third_party_client import third_party_client

logger = setup_logging("sync-service")


class SyncService:
    """同步服务类"""
    
    def __init__(self):
        self.client = third_party_client
    
    def generate_order_no(self, date: datetime) -> str:
        """
        生成订单编号
        格式: BFZ + 年月日 + 6位自增数字
        """
        date_str = date.strftime("%Y%m%d")
        # 这里应该从数据库获取当天的自增序号
        # 暂时使用时间戳的后6位作为序号
        seq = str(int(date.timestamp()))[-6:]
        return f"BFZ{date_str}{seq}"
    
    def parse_available_end_time(self, product_name: str) -> Optional[datetime]:
        """
        从产品名称中解析可用结束时间
        """
        try:
            # 查找日期模式，如 "2025年10月31日"
            import re
            pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日'
            match = re.search(pattern, product_name)
            
            if match:
                year, month, day = match.groups()
                return datetime(int(year), int(month), int(day))
                
            return None
        except Exception as e:
            logger.warning(f"解析产品名称中的日期失败: {product_name}, 错误: {str(e)}")
            return None
    
    async def sync_orders(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, int]:
        """
        同步订单数据
        """
        task_log = SyncTaskLogModel(
            task_name="sync_orders",
            task_type="ORDER_SYNC",
            start_time=datetime.now(),
            status="RUNNING"
        )
        
        success_count = 0
        error_count = 0
        error_messages = []
        
        try:
            async for db in get_db():
                # 保存任务日志
                db.add(task_log)
                await db.commit()
                
                # 获取订单列表
                orders = await self.client.get_order_list(start_date, end_date)
                
                for order_data in orders:
                    try:
                        await self._sync_single_order(db, order_data)
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        error_msg = f"同步订单失败 {order_data.get('order_reference', 'unknown')}: {str(e)}"
                        error_messages.append(error_msg)
                        logger.error(error_msg)
                        continue
                
                # 更新任务日志
                task_log.end_time = datetime.now()
                task_log.status = "COMPLETED" if error_count == 0 else "PARTIAL_SUCCESS"
                task_log.success_count = success_count
                task_log.error_count = error_count
                task_log.error_message = "; ".join(error_messages[:10])  # 只保存前10条错误信息
                
                await db.commit()
                
                logger.info(f"订单同步完成，成功: {success_count}, 失败: {error_count}")
                
                return {
                    "success_count": success_count,                            # 同步成功数量
                    "error_count": error_count,                                # 同步失败数量
                    "total_count": len(orders)                                 # 总订单数量
                }
                
        except Exception as e:
            task_log.end_time = datetime.now()
            task_log.status = "FAILED"
            task_log.error_message = str(e)
            
            async for db in get_db():
                await db.commit()
            
            logger.error(f"订单同步任务失败: {str(e)}")
            raise
    
    async def _sync_single_order(self, db: AsyncSession, order_data: Dict[str, Any]):
        """同步单个订单"""
        try:
            order_reference = order_data.get("order_reference")
            if not order_reference or not order_reference.startswith("D"):
                return
            
            # 检查订单是否已存在
            existing_order = await db.execute(
                select(OrderSyncModel).where(OrderSyncModel.external_no == order_reference)
            )
            existing = existing_order.scalar_one_or_none()
            
            # 获取订单详情
            order_detail = await self.client.get_order_detail(order_reference)
            
            # 生成订单编号
            create_time = datetime.fromisoformat(order_data.get("create_time", datetime.now().isoformat()))
            order_no = self.generate_order_no(create_time)
            
            # 处理支付单号
            pay_no = order_data.get("pay_no", "")
            if pay_no.startswith("S25"):
                pay_no = order_data.get("id", pay_no)
            
            # 获取微信支付信息
            wechat_info = await self.client.get_wechat_pay_info(pay_no) if pay_no else None
            customer_id = wechat_info.get("customer_id") if wechat_info else ""
            
            if existing:
                # 更新现有订单
                await db.execute(
                    update(OrderSyncModel)
                    .where(OrderSyncModel.external_no == order_reference)
                    .values(
                        external_order_status=order_detail.get("order_status"),
                        pay_status=order_data.get("pay_status"),
                        order_status=order_detail.get("order_status"),
                        pay_time=datetime.fromisoformat(order_data.get("pay_time")) if order_data.get("pay_time") else None,
                        arrival_time=datetime.fromisoformat(order_detail.get("pay_time")) if order_detail.get("pay_time") else None,
                        sync_status="UPDATED",
                        sync_time=datetime.now()
                    )
                )
            else:
                # 创建新订单记录
                new_order = OrderSyncModel(
                    order_no=order_no,                                         # 订单编号 BFZ+年月日+6位自增数字
                    external_no=order_reference,                               # 外部编号 来源系统的唯一编号
                    external_order_status=order_detail.get("order_status"),    # 外部订单状态
                    order_type="WEMINI",                                       # 订单类型 WEMINI/APP/OTHER
                    tenant_id="default",                                       # 租户ID
                    tenant_name="默认",                                         # 租户名称
                    customer_id=customer_id,                                   # 客户ID
                    create_time=create_time,                                   # 订单创建时间
                    pay_type="WECHAT",                                         # 支付类型 WECHAT/ALIPAY/OTHER
                    pay_time=datetime.fromisoformat(order_data.get("pay_time")) if order_data.get("pay_time") else None,  # 支付时间
                    arrival_time=datetime.fromisoformat(order_detail.get("pay_time")) if order_detail.get("pay_time") else None,  # 到账时间
                    pay_status=order_data.get("pay_status"),                   # 支付状态
                    order_status=order_detail.get("order_status"),             # 订单状态 UNPAY/UNUSE/USING/COMPT/REFD/UNDO
                    pay_no=pay_no,                                             # 支付单号
                    sync_status="SYNCED",                                      # 同步状态
                    sync_time=datetime.now()                                   # 同步时间
                )
                db.add(new_order)
            
            # 同步订单产品
            await self._sync_order_products(db, order_reference, order_no)
            
            await db.commit()
            
        except Exception as e:
            await db.rollback()
            raise e
    
    async def _sync_order_products(self, db: AsyncSession, order_reference: str, order_no: str):
        """同步订单产品"""
        try:
            # 获取对账明细
            reconciliation_details = await self.client.get_reconciliation_detail(order_reference)
            
            for detail in reconciliation_details:
                external_no = detail.get("order_detail_ind_reference")
                if not external_no or not external_no.startswith("m"):
                    continue
                
                # 检查产品是否已存在
                existing_product = await db.execute(
                    select(OrderProductSyncModel).where(
                        and_(
                            OrderProductSyncModel.order_no == order_no,
                            OrderProductSyncModel.external_no == external_no
                        )
                    )
                )
                existing = existing_product.scalar_one_or_none()
                
                if existing:
                    continue
                
                # 获取核验记录
                check_record = await self.client.get_check_record(external_no)
                
                # 解析产品名称中的可用结束时间
                product_name = detail.get("product_name", "")
                available_end_time = self.parse_available_end_time(product_name)
                
                # 获取客户联系方式
                customer_phone = ""
                if check_record:
                    customer_phone = check_record.get("tourist_phone", "")
                
                # 确定产品状态
                product_status = "UNUSE"
                verify_method = None
                verify_device_name = None
                use_time = None
                
                if check_record and check_record.get("use_status") == 1:
                    product_status = "COMPT"
                    verify_method = "CHECK"
                    verify_device_name = check_record.get("device_name")
                    use_time = datetime.fromisoformat(check_record.get("create_time")) if check_record.get("create_time") else None
                
                # 处理退款信息
                refund_way = detail.get("refund_way", 0)
                refund_status = "未退款" if refund_way == 0 else "已退款"
                
                # 创建订单产品记录
                new_product = OrderProductSyncModel(
                    order_no=order_no,                                         # 订单编号
                    product_id="default",                                      # 产品ID
                    product_name="默认",                                        # 产品名称
                    tenant_id="default",                                       # 租户ID
                    tenant_name="默认",                                         # 租户名称
                    external_no=external_no,                                   # 外部编号 m开头
                    category_level1="南京夫子庙",                                # 一级品类/业务领域
                    category_level4="联票",                                     # 四级品类
                    channel_commission_rate=0.0038,                            # 渠道佣金率
                    available_start_time=datetime.fromisoformat(detail.get("create_time")) if detail.get("create_time") else None,  # 可用开始时间
                    available_end_time=available_end_time,                     # 可用结束时间
                    channel_name="微信小程序",                                   # 渠道/分销名称
                    quantity=1,                                                # 产品数量
                    customer_phone=customer_phone,                             # 客户联系方式
                    product_status=product_status,                             # 产品状态 UNPAY/UNUSE/USING/COMPT/REFD/UNDO
                    verify_method=verify_method,                               # 核验方式 CHECK/FCHECK
                    verify_device="扫码机",                                     # 核验设备
                    verify_device_name=verify_device_name,                     # 核验设备账号名称
                    refund_method="REFD" if refund_way == 1 else "FREFD" if refund_way == 2 else None,  # 退款方式 REFD/FREFD
                    refund_status=refund_status,                               # 退款状态
                    refund_no=detail.get("serial_number"),                     # 退款编号
                    refund_reason=detail.get("cause"),                         # 退款原因
                    refund_time=datetime.fromisoformat(detail.get("create_time")) if detail.get("create_time") and refund_way != 0 else None,  # 退款时间
                    use_time=use_time,                                         # 产品使用时间
                    created_at=datetime.fromisoformat(detail.get("create_time")) if detail.get("create_time") else datetime.now()  # 记录创建时间
                )
                
                db.add(new_product)
            
        except Exception as e:
            logger.error(f"同步订单产品失败 {order_reference}: {str(e)}")
            raise
    
    async def get_sync_status(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取同步状态"""
        try:
            async for db in get_db():
                result = await db.execute(
                    select(SyncTaskLogModel)
                    .order_by(SyncTaskLogModel.created_at.desc())
                    .limit(limit)
                )
                logs = result.scalars().all()
                
                return [
                    {
                        "id": log.id,                                           # 日志ID
                        "task_name": log.task_name,                             # 任务名称
                        "task_type": log.task_type,                             # 任务类型
                        "start_time": log.start_time.isoformat(),               # 开始时间
                        "end_time": log.end_time.isoformat() if log.end_time else None,  # 结束时间
                        "status": log.status,                                   # 执行状态
                        "success_count": log.success_count,                     # 成功数量
                        "error_count": log.error_count,                         # 失败数量
                        "error_message": log.error_message                      # 错误信息
                    }
                    for log in logs
                ]
        except Exception as e:
            logger.error(f"获取同步状态失败: {str(e)}")
            raise


# 创建全局同步服务实例
sync_service = SyncService()