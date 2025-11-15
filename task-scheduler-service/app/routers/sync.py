"""
数据同步相关路由
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../shared'))
from ..models import BaseResponse
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../shared'))
from utils import format_response

from ..database import (
    get_db, OrderSyncModel, OrderProductSyncModel, 
    ProductModel, OrganizationModel
)

router = APIRouter()


@router.get("/orders", response_model=BaseResponse)
async def get_synced_orders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    order_status: Optional[str] = Query(None, description="订单状态"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    external_no: Optional[str] = Query(None, description="外部订单号"),
    db: AsyncSession = Depends(get_db)
):
    """获取同步的订单列表"""
    try:
        # 构建查询条件
        conditions = []
        
        if order_status:
            conditions.append(OrderSyncModel.order_status == order_status)
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            conditions.append(OrderSyncModel.create_time >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            conditions.append(OrderSyncModel.create_time <= end_dt)
        
        if external_no:
            conditions.append(OrderSyncModel.external_no.ilike(f"%{external_no}%"))
        
        # 查询总数
        count_query = select(func.count(OrderSyncModel.order_no))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 分页查询
        query = select(OrderSyncModel).order_by(desc(OrderSyncModel.created_at))
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        orders = result.scalars().all()
        
        # 转换数据格式
        order_list = []
        for order in orders:
            order_dict = {
                "order_no": order.order_no,                    # 订单编号 BFZ+年月日+6位自增数字
                "external_no": order.external_no,              # 外部编号 来源系统的唯一编号
                "external_order_status": order.external_order_status,  # 外部订单状态
                "order_type": order.order_type,                # 订单类型 WEMINI/APP/OTHER
                "tenant_id": order.tenant_id,                  # 租户ID
                "tenant_name": order.tenant_name,              # 租户名称
                "customer_id": order.customer_id,              # 客户ID
                "create_time": order.create_time.isoformat() if order.create_time else None,  # 订单创建时间
                "pay_type": order.pay_type,                    # 支付类型 WECHAT/ALIPAY/OTHER
                "pay_time": order.pay_time.isoformat() if order.pay_time else None,          # 支付时间
                "arrival_time": order.arrival_time.isoformat() if order.arrival_time else None,  # 到账时间
                "pay_status": order.pay_status,                # 支付状态
                "order_status": order.order_status,            # 订单状态 UNPAY/UNUSE/USING/COMPT/REFD/UNDO
                "pay_no": order.pay_no,                        # 支付单号
                "order_amount": float(order.order_amount) if order.order_amount else 0,      # 订单金额
                "refund_amount": float(order.refund_amount) if order.refund_amount else 0,   # 退款金额
                "product_count": order.product_count,          # 产品数量
                "sync_status": order.sync_status,              # 同步状态
                "sync_time": order.sync_time.isoformat() if order.sync_time else None,      # 同步时间
                "created_at": order.created_at.isoformat(),    # 记录创建时间
                "updated_at": order.updated_at.isoformat()     # 记录更新时间
            }
            order_list.append(order_dict)
        
        return format_response(
            message="获取订单列表成功",
            data={
                "orders": order_list,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取订单列表失败: {str(e)}"
        )


@router.get("/orders/{order_no}/products", response_model=BaseResponse)
async def get_order_products(
    order_no: str,
    db: AsyncSession = Depends(get_db)
):
    """获取订单的产品列表"""
    try:
        # 查询订单产品
        query = select(OrderProductSyncModel).where(
            OrderProductSyncModel.order_no == order_no
        ).order_by(OrderProductSyncModel.created_at)
        
        result = await db.execute(query)
        products = result.scalars().all()
        
        if not products:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到该订单的产品信息"
            )
        
        # 转换数据格式
        product_list = []
        for product in products:
            product_dict = {
                "id": product.id,                              # 订单产品编号
                "order_no": product.order_no,                  # 订单编号
                "external_no": product.external_no,            # 外部编号 m开头
                "product_id": product.product_id,              # 产品ID
                "product_name": product.product_name,          # 产品名称
                "category_level1": product.category_level1,    # 一级品类/业务领域
                "category_level4": product.category_level4,    # 四级品类
                "channel_name": product.channel_name,          # 渠道/分销名称
                "quantity": product.quantity,                  # 产品数量
                "customer_name": product.customer_name,        # 客户名称
                "customer_phone": product.customer_phone,      # 客户联系方式
                "product_status": product.product_status,      # 产品状态 UNPAY/UNUSE/USING/COMPT/REFD/UNDO
                "verify_method": product.verify_method,        # 核验方式 CHECK/FCHECK
                "verify_device_name": product.verify_device_name,  # 核验设备账号名称
                "refund_status": product.refund_status,        # 退款状态
                "refund_amount": float(product.actual_refund_amount) if product.actual_refund_amount else 0,  # 实际退款金额
                "use_time": product.use_time.isoformat() if product.use_time else None,                      # 产品使用时间
                "available_start_time": product.available_start_time.isoformat() if product.available_start_time else None,  # 可用开始时间
                "available_end_time": product.available_end_time.isoformat() if product.available_end_time else None,        # 可用结束时间
                "created_at": product.created_at.isoformat(),  # 记录创建时间
                "updated_at": product.updated_at.isoformat()   # 记录更新时间
            }
            product_list.append(product_dict)
        
        return format_response(
            message="获取订单产品列表成功",
            data=product_list
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取订单产品列表失败: {str(e)}"
        )


@router.get("/statistics", response_model=BaseResponse)
async def get_sync_statistics(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db)
):
    """获取同步统计信息"""
    try:
        # 构建时间条件
        conditions = []
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            conditions.append(OrderSyncModel.create_time >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            conditions.append(OrderSyncModel.create_time <= end_dt)
        
        # 订单统计 - 统计订单数量、金额等信息
        order_query = select(
            func.count(OrderSyncModel.order_no).label("total_orders"),           # 订单总数
            func.sum(OrderSyncModel.order_amount).label("total_amount"),         # 订单总金额
            func.sum(OrderSyncModel.refund_amount).label("total_refund"),        # 退款总金额
            func.count().filter(OrderSyncModel.order_status == 'COMPT').label("completed_orders"),  # 已完成订单数
            func.count().filter(OrderSyncModel.order_status == 'REFD').label("refunded_orders")     # 已退款订单数
        )
        
        if conditions:
            order_query = order_query.where(and_(*conditions))
        
        order_result = await db.execute(order_query)
        order_stats = order_result.first()
        
        # 产品统计 - 统计产品使用和退款情况
        product_query = select(
            func.count(OrderProductSyncModel.id).label("total_products"),        # 产品总数
            func.count().filter(OrderProductSyncModel.product_status == 'COMPT').label("used_products"),      # 已使用产品数
            func.count().filter(OrderProductSyncModel.refund_status == '已退款').label("refunded_products")   # 已退款产品数
        )
        
        # 如果有时间条件，需要关联订单表进行过滤
        if conditions:
            product_query = product_query.join(
                OrderSyncModel, OrderProductSyncModel.order_no == OrderSyncModel.order_no
            ).where(and_(*conditions))
        
        product_result = await db.execute(product_query)
        product_stats = product_result.first()
        
        # 按状态统计订单 - 统计各状态订单数量
        status_query = select(
            OrderSyncModel.order_status,                                         # 订单状态
            func.count(OrderSyncModel.order_no).label("count")                   # 该状态订单数量
        ).group_by(OrderSyncModel.order_status)
        
        if conditions:
            status_query = status_query.where(and_(*conditions))
        
        status_result = await db.execute(status_query)
        status_stats = status_result.all()
        
        return format_response(
            message="获取统计信息成功",
            data={
                "order_statistics": {                                            # 订单统计信息
                    "total_orders": order_stats.total_orders or 0,              # 订单总数
                    "total_amount": float(order_stats.total_amount or 0),       # 订单总金额
                    "total_refund": float(order_stats.total_refund or 0),       # 退款总金额
                    "completed_orders": order_stats.completed_orders or 0,      # 已完成订单数
                    "refunded_orders": order_stats.refunded_orders or 0         # 已退款订单数
                },
                "product_statistics": {                                          # 产品统计信息
                    "total_products": product_stats.total_products or 0,        # 产品总数
                    "used_products": product_stats.used_products or 0,          # 已使用产品数
                    "refunded_products": product_stats.refunded_products or 0   # 已退款产品数
                },
                "status_distribution": [                                         # 订单状态分布
                    {
                        "status": stat.order_status,                            # 订单状态
                        "count": stat.count                                     # 该状态订单数量
                    }
                    for stat in status_stats
                ]
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )