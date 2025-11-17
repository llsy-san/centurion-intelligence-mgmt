#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务服务测试脚本
用于验证服务的核心功能
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# 添加路径
current_dir = os.path.dirname(__file__)
shared_dir = os.path.join(current_dir, '..', 'shared')
sys.path.insert(0, shared_dir)

try:
    from utils import setup_logging
except ImportError:
    # 如果无法导入，使用简单的日志配置
    import logging
    def setup_logging(name):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(name)

logger = setup_logging("test-service")


class MockThirdPartyClient:
    """模拟第三方API客户端"""
    
    async def get_order_list(self, start_date=None, end_date=None):
        """模拟获取订单列表"""
        logger.info(f"模拟获取订单列表: {start_date} to {end_date}")
        return [
            {
                "order_reference": "D20241112001",
                "create_time": "2024-11-12T10:00:00",
                "pay_time": "2024-11-12T10:05:00",
                "pay_status": "PAID",
                "pay_no": "PAY20241112001",
                "id": "12345"
            },
            {
                "order_reference": "D20241112002",
                "create_time": "2024-11-12T11:00:00",
                "pay_time": "2024-11-12T11:05:00",
                "pay_status": "PAID",
                "pay_no": "S2520241112002",
                "id": "12346"
            }
        ]
    
    async def get_order_detail(self, order_reference):
        """模拟获取订单详情"""
        logger.info(f"模拟获取订单详情: {order_reference}")
        return {
            "order_status": "COMPT",
            "pay_time": "2024-11-12T10:05:00"
        }
    
    async def get_wechat_pay_info(self, pay_no):
        """模拟获取微信支付信息"""
        logger.info(f"模拟获取微信支付信息: {pay_no}")
        return {
            "customer_id": "wx_openid_123456"
        }
    
    async def get_reconciliation_detail(self, order_reference):
        """模拟获取对账明细"""
        logger.info(f"模拟获取对账明细: {order_reference}")
        return [
            {
                "order_detail_ind_reference": "m20241112001",
                "product_name": "【苏超特惠】南京夫子庙大成殿＋中国科举博物馆-2025年10月31日",
                "create_time": "2024-11-12T10:00:00",
                "refund_way": 0,
                "serial_number": "",
                "cause": ""
            }
        ]
    
    async def get_check_record(self, external_no):
        """模拟获取核验记录"""
        logger.info(f"模拟获取核验记录: {external_no}")
        # 模拟部分产品已使用
        if external_no.endswith("001"):
            return {
                "use_status": 1,
                "device_name": "扫码机001",
                "tourist_phone": "13800138000",
                "create_time": "2024-11-12T14:00:00"
            }
        return None


class MockSyncService:
    """模拟同步服务"""
    
    def __init__(self):
        self.client = MockThirdPartyClient()
    
    def generate_order_no(self, date: datetime) -> str:
        """生成订单编号"""
        date_str = date.strftime("%Y%m%d")
        seq = str(int(date.timestamp()))[-6:]
        return f"BFZ{date_str}{seq}"
    
    def parse_available_end_time(self, product_name: str):
        """解析产品有效期"""
        import re
        pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日'
        match = re.search(pattern, product_name)
        
        if match:
            year, month, day = match.groups()
            return datetime(int(year), int(month), int(day))
        return None
    
    async def sync_orders(self, start_date=None, end_date=None):
        """模拟同步订单"""
        logger.info("开始模拟订单同步...")
        
        try:
            # 获取订单列表
            orders = await self.client.get_order_list(start_date, end_date)
            logger.info(f"获取到 {len(orders)} 个订单")
            
            success_count = 0
            error_count = 0
            
            for order_data in orders:
                try:
                    await self._sync_single_order(order_data)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    logger.error(f"同步订单失败 {order_data.get('order_reference')}: {str(e)}")
            
            result = {
                "success_count": success_count,
                "error_count": error_count,
                "total_count": len(orders)
            }
            
            logger.info(f"订单同步完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"订单同步任务失败: {str(e)}")
            raise
    
    async def _sync_single_order(self, order_data):
        """模拟同步单个订单"""
        order_reference = order_data.get("order_reference")
        logger.info(f"同步订单: {order_reference}")
        
        # 生成订单编号
        create_time = datetime.fromisoformat(order_data.get("create_time"))
        order_no = self.generate_order_no(create_time)
        logger.info(f"生成订单编号: {order_no}")
        
        # 获取订单详情
        order_detail = await self.client.get_order_detail(order_reference)
        logger.info(f"订单详情: {order_detail}")
        
        # 获取微信支付信息
        pay_no = order_data.get("pay_no", "")
        if pay_no.startswith("S25"):
            pay_no = order_data.get("id", pay_no)
        
        wechat_info = await self.client.get_wechat_pay_info(pay_no)
        logger.info(f"微信支付信息: {wechat_info}")
        
        # 同步订单产品
        await self._sync_order_products(order_reference, order_no)
    
    async def _sync_order_products(self, order_reference, order_no):
        """模拟同步订单产品"""
        logger.info(f"同步订单产品: {order_reference}")
        
        # 获取对账明细
        reconciliation_details = await self.client.get_reconciliation_detail(order_reference)
        logger.info(f"对账明细: {len(reconciliation_details)} 个产品")
        
        for detail in reconciliation_details:
            external_no = detail.get("order_detail_ind_reference")
            logger.info(f"处理产品: {external_no}")
            
            # 获取核验记录
            check_record = await self.client.get_check_record(external_no)
            
            # 解析产品有效期
            product_name = detail.get("product_name", "")
            available_end_time = self.parse_available_end_time(product_name)
            
            # 确定产品状态
            product_status = "UNUSE"
            if check_record and check_record.get("use_status") == 1:
                product_status = "COMPT"
            
            logger.info(f"产品状态: {product_status}, 有效期: {available_end_time}")


async def test_sync_service():
    """测试同步服务"""
    logger.info("=" * 50)
    logger.info("开始测试定时任务服务")
    logger.info("=" * 50)
    
    # 创建模拟同步服务
    sync_service = MockSyncService()
    
    # 测试订单同步
    end_time = datetime.now()
    start_time = end_time - timedelta(days=1)
    
    logger.info(f"测试时间范围: {start_time} 到 {end_time}")
    
    try:
        result = await sync_service.sync_orders(start_time, end_time)
        logger.info("=" * 50)
        logger.info("测试结果:")
        logger.info(f"成功同步: {result['success_count']} 个订单")
        logger.info(f"同步失败: {result['error_count']} 个订单")
        logger.info(f"总计订单: {result['total_count']} 个订单")
        logger.info("=" * 50)
        logger.info("定时任务服务测试完成!")
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        raise


def test_data_parsing():
    """测试数据解析功能"""
    logger.info("测试数据解析功能...")
    
    sync_service = MockSyncService()
    
    # 测试订单编号生成
    test_date = datetime(2024, 11, 12, 10, 0, 0)
    order_no = sync_service.generate_order_no(test_date)
    logger.info(f"生成订单编号: {order_no}")
    assert order_no.startswith("BFZ20241112"), f"订单编号格式错误: {order_no}"
    
    # 测试产品有效期解析
    test_products = [
        "【苏超特惠】南京夫子庙大成殿＋中国科举博物馆-2025年10月31日",
        "【苏超特惠】南京夫子庙大成殿＋中国科举博物馆-2025年11月30日",
        "【黑科技MR单人票】夫子庙户外混合现实游戏-2026年8月15日"
    ]
    
    for product_name in test_products:
        end_time = sync_service.parse_available_end_time(product_name)
        logger.info(f"产品: {product_name[:30]}... -> 有效期: {end_time}")
        assert end_time is not None, f"解析有效期失败: {product_name}"
    
    logger.info("数据解析功能测试通过!")


if __name__ == "__main__":
    logger.info("定时任务服务功能测试开始")
    
    # 测试数据解析
    test_data_parsing()
    
    # 测试同步服务
    asyncio.run(test_sync_service())
    
    logger.info("所有测试完成!")