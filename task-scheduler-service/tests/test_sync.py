"""
定时任务服务测试
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../app'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))

from app.services.sync_service import SyncService
from app.services.third_party_client import ThirdPartyClient


@pytest.mark.asyncio
class TestSyncService:
    """同步服务测试类"""
    
    def setup_method(self):
        """测试前置设置"""
        self.sync_service = SyncService()
    
    def test_generate_order_no(self):
        """测试订单编号生成"""
        test_date = datetime(2025, 1, 15, 10, 30, 0)
        order_no = self.sync_service.generate_order_no(test_date)
        
        assert order_no.startswith("BFZ20250115")
        assert len(order_no) == 17  # BFZ + 8位日期 + 6位序号
    
    def test_parse_available_end_time(self):
        """测试解析产品名称中的日期"""
        product_name = "【苏超特惠】南京夫子庙大成殿＋中国科举博物馆＋李香君故居+王导谢安纪念馆+秦状元府+文创冰淇淋-2025年10月31日"
        
        end_time = self.sync_service.parse_available_end_time(product_name)
        
        assert end_time is not None
        assert end_time.year == 2025
        assert end_time.month == 10
        assert end_time.day == 31
    
    def test_parse_available_end_time_no_date(self):
        """测试解析不包含日期的产品名称"""
        product_name = "普通产品名称"
        
        end_time = self.sync_service.parse_available_end_time(product_name)
        
        assert end_time is None
    
    @patch('app.services.sync_service.get_db')
    @patch('app.services.sync_service.third_party_client')
    async def test_sync_orders(self, mock_client, mock_get_db):
        """测试订单同步"""
        # 模拟数据库会话
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db
        
        # 模拟第三方API返回数据
        mock_orders = [
            {
                "order_reference": "D123456789",
                "create_time": "2025-01-15T10:30:00",
                "pay_time": "2025-01-15T10:35:00",
                "pay_status": "PAID",
                "pay_no": "WX123456789"
            }
        ]
        
        mock_client.get_order_list.return_value = mock_orders
        mock_client.get_order_detail.return_value = {
            "order_status": "COMPT",
            "pay_time": "2025-01-15T10:35:00"
        }
        mock_client.get_reconciliation_detail.return_value = []
        mock_client.get_wechat_pay_info.return_value = {
            "customer_id": "wx_openid_123456"
        }
        
        # 模拟数据库查询返回空结果（新订单）
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        # 执行同步
        result = await self.sync_service.sync_orders()
        
        # 验证结果
        assert result["success_count"] == 1
        assert result["error_count"] == 0
        assert result["total_count"] == 1
        
        # 验证调用了相关方法
        mock_client.get_order_list.assert_called_once()
        mock_client.get_order_detail.assert_called_once_with("D123456789")


@pytest.mark.asyncio
class TestThirdPartyClient:
    """第三方客户端测试类"""
    
    def setup_method(self):
        """测试前置设置"""
        self.client = ThirdPartyClient("https://api.test.com", "test-key")
    
    async def teardown_method(self):
        """测试后置清理"""
        await self.client.close()
    
    @patch('httpx.AsyncClient.get')
    async def test_get_order_list_success(self, mock_get):
        """测试获取订单列表成功"""
        # 模拟HTTP响应
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "data": [
                {"order_reference": "D123456789", "create_time": "2025-01-15T10:30:00"}
            ]
        }
        mock_get.return_value = mock_response
        
        # 执行测试
        orders = await self.client.get_order_list()
        
        # 验证结果
        assert len(orders) == 1
        assert orders[0]["order_reference"] == "D123456789"
        
        # 验证HTTP调用
        mock_get.assert_called_once()
    
    @patch('httpx.AsyncClient.get')
    async def test_get_order_detail_success(self, mock_get):
        """测试获取订单详情成功"""
        # 模拟HTTP响应
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "data": {"order_status": "COMPT", "pay_time": "2025-01-15T10:35:00"}
        }
        mock_get.return_value = mock_response
        
        # 执行测试
        detail = await self.client.get_order_detail("D123456789")
        
        # 验证结果
        assert detail["order_status"] == "COMPT"
        assert detail["pay_time"] == "2025-01-15T10:35:00"


if __name__ == "__main__":
    pytest.main([__file__])