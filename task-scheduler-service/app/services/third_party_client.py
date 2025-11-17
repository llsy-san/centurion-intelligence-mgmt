# -*- coding: utf-8 -*-
"""
第三方API客户端
模拟第三方系统的API调用
"""
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from ..utils import setup_logging

logger = setup_logging("third-party-client")


class ThirdPartyClient:
    """第三方API客户端"""
    
    def __init__(self, base_url: str = "https://api.example.com"):
        self.base_url = base_url
        self.session = None
    
    async def _get_session(self):
        """获取HTTP会话"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
    
    async def close(self):
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()
    
    async def get_order_list(self, start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """
        获取订单列表
        模拟第三方API调用
        """
        try:
            # 模拟API调用延迟
            await asyncio.sleep(0.1)
            
            # 模拟返回数据
            mock_orders = [
                {
                    "order_reference": "D20241101001",
                    "create_time": "2024-11-01T10:00:00",
                    "pay_status": "PAID",
                    "pay_time": "2024-11-01T10:05:00",
                    "pay_no": "S2520241101001",
                    "id": "order_001"
                },
                {
                    "order_reference": "D20241101002", 
                    "create_time": "2024-11-01T11:00:00",
                    "pay_status": "PAID",
                    "pay_time": "2024-11-01T11:05:00",
                    "pay_no": "S2520241101002",
                    "id": "order_002"
                }
            ]
            
            logger.info(f"获取订单列表成功，共 {len(mock_orders)} 条记录")
            return mock_orders
            
        except Exception as e:
            logger.error(f"获取订单列表失败: {str(e)}")
            raise
    
    async def get_order_detail(self, order_reference: str) -> Dict[str, Any]:
        """
        获取订单详情
        """
        try:
            await asyncio.sleep(0.05)
            
            # 模拟订单详情数据
            mock_detail = {
                "order_reference": order_reference,
                "order_status": "COMPT",
                "pay_time": "2024-11-01T10:05:00",
                "total_amount": 100.00,
                "refund_amount": 0.00,
                "product_count": 1
            }
            
            logger.debug(f"获取订单详情成功: {order_reference}")
            return mock_detail
            
        except Exception as e:
            logger.error(f"获取订单详情失败 {order_reference}: {str(e)}")
            raise
    
    async def get_wechat_pay_info(self, pay_no: str) -> Dict[str, Any]:
        """
        获取微信支付信息
        """
        try:
            await asyncio.sleep(0.05)
            
            # 模拟微信支付信息
            mock_pay_info = {
                "pay_no": pay_no,
                "customer_id": f"wx_customer_{pay_no[-3:]}",
                "pay_method": "WECHAT",
                "pay_status": "SUCCESS"
            }
            
            logger.debug(f"获取微信支付信息成功: {pay_no}")
            return mock_pay_info
            
        except Exception as e:
            logger.error(f"获取微信支付信息失败 {pay_no}: {str(e)}")
            raise
    
    async def get_reconciliation_detail(self, order_reference: str) -> List[Dict[str, Any]]:
        """
        获取对账明细
        """
        try:
            await asyncio.sleep(0.05)
            
            # 模拟对账明细数据
            mock_details = [
                {
                    "order_detail_ind_reference": f"m{order_reference[1:]}001",
                    "product_name": "南京夫子庙联票（有效期至2025年10月31日）",
                    "create_time": "2024-11-01T10:00:00",
                    "refund_way": 0,  # 0-未退款, 1-已退款, 2-部分退款
                    "serial_number": "",
                    "cause": ""
                }
            ]
            
            logger.debug(f"获取对账明细成功: {order_reference}")
            return mock_details
            
        except Exception as e:
            logger.error(f"获取对账明细失败 {order_reference}: {str(e)}")
            raise
    
    async def get_check_record(self, external_no: str) -> Optional[Dict[str, Any]]:
        """
        获取核验记录
        """
        try:
            await asyncio.sleep(0.05)
            
            # 模拟核验记录（50%概率有核验记录）
            if hash(external_no) % 2 == 0:
                mock_record = {
                    "external_no": external_no,
                    "use_status": 1,  # 1-已使用, 0-未使用
                    "device_name": "扫码机001",
                    "tourist_phone": "138****1234",
                    "create_time": "2024-11-01T14:30:00"
                }
                logger.debug(f"获取核验记录成功: {external_no}")
                return mock_record
            else:
                logger.debug(f"未找到核验记录: {external_no}")
                return None
                
        except Exception as e:
            logger.error(f"获取核验记录失败 {external_no}: {str(e)}")
            raise


# 创建全局客户端实例
third_party_client = ThirdPartyClient()