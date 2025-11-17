"""
同步服务
处理第三方数据同步逻辑
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..utils import setup_logging
from .third_party_client import third_party_client

logger = setup_logging("sync-service")


class SyncService:
    """同步服务类"""
    
    def __init__(self):
        self.client = third_party_client
    
    async def sync_orders(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, int]:
        """
        同步订单数据
        """
        success_count = 0
        error_count = 0
        
        try:
            # 设置默认时间范围
            if end_date is None:
                end_date = datetime.now()
            if start_date is None:
                start_date = end_date - timedelta(hours=24)
            
            logger.info(f"开始同步订单数据，时间范围: {start_date} - {end_date}")
            
            # 获取订单列表
            orders = await self.client.get_order_list(start_date, end_date)
            
            for order_data in orders:
                try:
                    await self._process_single_order(order_data)
                    success_count += 1
                    logger.debug(f"订单同步成功: {order_data.get('order_reference', 'unknown')}")
                except Exception as e:
                    error_count += 1
                    logger.error(f"订单同步失败 {order_data.get('order_reference', 'unknown')}: {str(e)}")
                    continue
            
            logger.info(f"订单同步完成，成功: {success_count}, 失败: {error_count}")
            
            return {
                "success_count": success_count,
                "error_count": error_count,
                "total_count": len(orders)
            }
                
        except Exception as e:
            logger.error(f"订单同步任务失败: {str(e)}")
            raise
    
    async def _process_single_order(self, order_data: Dict[str, Any]):
        """处理单个订单"""
        try:
            order_reference = order_data.get("order_reference")
            if not order_reference or not order_reference.startswith("D"):
                return
            
            # 获取订单详情
            order_detail = await self.client.get_order_detail(order_reference)
            
            # 获取对账明细 
            reconciliation_details = await self.client.get_reconciliation_detail(order_reference)
            
            # 处理订单产品
            for detail in reconciliation_details:
                external_no = detail.get("order_detail_ind_reference")
                if external_no and external_no.startswith("m"):
                    # 获取核验记录
                    check_record = await self.client.get_check_record(external_no)
                    logger.debug(f"处理产品: {external_no}, 核验状态: {'已使用' if check_record else '未使用'}")
            
            logger.debug(f"订单处理完成: {order_reference}")
            
        except Exception as e:
            logger.error(f"处理订单失败 {order_data.get('order_reference', 'unknown')}: {str(e)}")
            raise
    
    async def get_sync_status(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取同步状态"""
        try:
            # 模拟返回同步日志
            mock_logs = []
            for i in range(min(limit, 5)):
                log_time = datetime.now() - timedelta(hours=i)
                mock_logs.append({
                    "id": f"log_{i+1}",
                    "task_name": "sync_orders",
                    "task_type": "ORDER_SYNC", 
                    "start_time": log_time.isoformat(),
                    "end_time": (log_time + timedelta(minutes=5)).isoformat(),
                    "status": "COMPLETED" if i % 3 != 2 else "PARTIAL_SUCCESS",
                    "success_count": 10 - i,
                    "error_count": i,
                    "error_message": f"部分同步失败" if i % 3 == 2 else None
                })
            
            return mock_logs
            
        except Exception as e:
            logger.error(f"获取同步状态失败: {str(e)}")
            raise


# 创建全局同步服务实例
sync_service = SyncService()