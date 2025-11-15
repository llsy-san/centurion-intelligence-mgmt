"""
第三方系统客户端
用于从第三方系统获取订单数据
"""
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../shared'))
from utils import setup_logging

logger = setup_logging("third-party-client")


class ThirdPartyClient:
    """第三方系统客户端"""
    
    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
    
    async def get_order_list(self, start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """
        获取订单列表
        从第三方系统获取订单数据
        """
        try:
            # 如果没有指定时间范围，默认获取最近7天的数据
            if not start_date:
                start_date = datetime.now() - timedelta(days=7)
            if not end_date:
                end_date = datetime.now()
            
            params = {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "page": 1,
                "page_size": 1000
            }
            
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            # 模拟第三方API调用
            # 实际使用时需要替换为真实的API端点
            url = f"{self.base_url}/api/orders/list"
            
            logger.info(f"正在获取订单列表，参数: {params}")
            
            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            orders = data.get("data", [])
            
            logger.info(f"成功获取 {len(orders)} 条订单数据")
            return orders
            
        except Exception as e:
            logger.error(f"获取订单列表失败: {str(e)}")
            raise
    
    async def get_order_detail(self, order_reference: str) -> Dict[str, Any]:
        """
        获取订单详情
        根据订单编号获取详细信息
        """
        try:
            url = f"{self.base_url}/api/orders/{order_reference}/detail"
            
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            logger.info(f"正在获取订单详情: {order_reference}")
            
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            return data.get("data", {})
            
        except Exception as e:
            logger.error(f"获取订单详情失败 {order_reference}: {str(e)}")
            raise
    
    async def get_reconciliation_detail(self, order_reference: str) -> List[Dict[str, Any]]:
        """
        获取对账明细
        从pw_reconciliation_amount_detail接口获取数据
        """
        try:
            url = f"{self.base_url}/api/reconciliation/detail"
            
            params = {
                "order_reference": order_reference
            }
            
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            logger.info(f"正在获取对账明细: {order_reference}")
            
            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            return data.get("data", [])
            
        except Exception as e:
            logger.error(f"获取对账明细失败 {order_reference}: {str(e)}")
            raise
    
    async def get_check_record(self, external_no: str) -> Optional[Dict[str, Any]]:
        """
        获取核验记录
        从check_record接口获取核验信息
        """
        try:
            url = f"{self.base_url}/api/check/record"
            
            params = {
                "external_no": external_no
            }
            
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            logger.info(f"正在获取核验记录: {external_no}")
            
            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            records = data.get("data", [])
            
            # 返回第一条记录，如果存在的话
            return records[0] if records else None
            
        except Exception as e:
            logger.error(f"获取核验记录失败 {external_no}: {str(e)}")
            return None
    
    async def get_wechat_pay_info(self, pay_no: str) -> Optional[Dict[str, Any]]:
        """
        从微信支付平台获取支付信息
        """
        try:
            # 这里应该调用微信支付API
            # 暂时返回模拟数据
            logger.info(f"正在从微信支付平台获取支付信息: {pay_no}")
            
            # 模拟数据
            return {
                "customer_id": "wx_openid_123456",
                "apply_refund_amount": 0,
                "actual_refund_amount": 0
            }
            
        except Exception as e:
            logger.error(f"获取微信支付信息失败 {pay_no}: {str(e)}")
            return None


# 创建全局客户端实例
third_party_client = ThirdPartyClient(
    base_url="https://api.third-party.com",  # 替换为实际的第三方API地址
    api_key="your-api-key"  # 替换为实际的API密钥
)