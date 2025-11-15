"""
订单通用查询接口
基于同步的数据提供查询服务
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, text
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../shared'))
from ..models import BaseResponse
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../shared'))
from utils import format_response

from ..database import get_db

router = APIRouter()


@router.get("/orders/search", response_model=BaseResponse)
async def search_orders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    order_no: Optional[str] = Query(None, description="订单编号"),
    external_no: Optional[str] = Query(None, description="外部订单号"),
    customer_id: Optional[str] = Query(None, description="客户ID"),
    order_status: Optional[str] = Query(None, description="订单状态"),
    pay_status: Optional[str] = Query(None, description="支付状态"),
    tenant_id: Optional[str] = Query(None, description="租户ID"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db)
):
    """通用订单查询接口"""
    try:
        # 构建查询SQL - 直接查询同步表
        base_query = """
        SELECT 
            order_no,
            external_no,
            external_order_status,
            order_type,
            tenant_id,
            tenant_name,
            customer_id,
            create_time,
            pay_type,
            pay_time,
            arrival_time,
            pay_status,
            order_status,
            pay_no,
            order_amount,
            refund_amount,
            settlement_amount,
            product_count,
            sync_status,
            created_at,
            updated_at
        FROM order_sync
        WHERE 1=1
        """
        
        count_query = "SELECT COUNT(*) FROM order_sync WHERE 1=1"
        
        conditions = []
        params = {}
        
        # 添加查询条件
        if order_no:
            conditions.append("AND order_no ILIKE :order_no")
            params["order_no"] = f"%{order_no}%"
        
        if external_no:
            conditions.append("AND external_no ILIKE :external_no")
            params["external_no"] = f"%{external_no}%"
        
        if customer_id:
            conditions.append("AND customer_id = :customer_id")
            params["customer_id"] = customer_id
        
        if order_status:
            conditions.append("AND order_status = :order_status")
            params["order_status"] = order_status
        
        if pay_status:
            conditions.append("AND pay_status = :pay_status")
            params["pay_status"] = pay_status
        
        if tenant_id:
            conditions.append("AND tenant_id = :tenant_id")
            params["tenant_id"] = tenant_id
        
        if start_date:
            conditions.append("AND create_time >= :start_date")
            params["start_date"] = start_date
        
        if end_date:
            conditions.append("AND create_time <= :end_date")
            params["end_date"] = end_date
        
        # 组装完整查询
        where_clause = " ".join(conditions)
        full_query = base_query + where_clause + " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        full_count_query = count_query + where_clause
        
        params["limit"] = page_size
        params["offset"] = (page - 1) * page_size
        
        # 执行查询
        count_result = await db.execute(text(full_count_query), params)
        total = count_result.scalar()
        
        result = await db.execute(text(full_query), params)
        orders = result.fetchall()
        
        # 转换数据格式
        order_list = []
        for order in orders:
            order_dict = {
                "order_no": order.order_no,
                "external_no": order.external_no,
                "external_order_status": order.external_order_status,
                "order_type": order.order_type,
                "tenant_id": order.tenant_id,
                "tenant_name": order.tenant_name,
                "customer_id": order.customer_id,
                "create_time": order.create_time.isoformat() if order.create_time else None,
                "pay_type": order.pay_type,
                "pay_time": order.pay_time.isoformat() if order.pay_time else None,
                "arrival_time": order.arrival_time.isoformat() if order.arrival_time else None,
                "pay_status": order.pay_status,
                "order_status": order.order_status,
                "pay_no": order.pay_no,
                "order_amount": float(order.order_amount) if order.order_amount else 0,
                "refund_amount": float(order.refund_amount) if order.refund_amount else 0,
                "settlement_amount": float(order.settlement_amount) if order.settlement_amount else 0,
                "product_count": order.product_count,
                "sync_status": order.sync_status,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat()
            }
            order_list.append(order_dict)
        
        return format_response(
            message="查询订单成功",
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
            detail=f"查询订单失败: {str(e)}"
        )


@router.get("/orders/{order_no}", response_model=BaseResponse)
async def get_order_detail(
    order_no: str,
    db: AsyncSession = Depends(get_db)
):
    """获取订单详情"""
    try:
        # 查询订单基本信息
        order_query = """
        SELECT 
            order_no, external_no, external_order_status, order_type,
            tenant_id, tenant_name, customer_id, create_time, pay_type,
            pay_time, arrival_time, pay_status, order_status, pay_no,
            order_amount, refund_amount, settlement_amount, product_count,
            avg_price, channel_fee, mailing_address, mailing_status,
            hotel_confirm_no, sync_status, sync_time, created_at, updated_at
        FROM order_sync 
        WHERE order_no = :order_no OR external_no = :order_no
        """
        
        result = await db.execute(text(order_query), {"order_no": order_no})
        order = result.fetchone()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到该订单"
            )
        
        # 查询订单产品
        products_query = """
        SELECT 
            id, external_no, product_id, product_name, category_level1,
            category_level2, category_level3, category_level4, category_level5,
            channel_price, channel_commission_rate, available_start_time,
            available_end_time, channel_id, channel_name, quantity,
            customer_name, customer_phone, customer_id_card, product_status,
            verify_method, verify_device, verify_device_name, refund_status,
            refund_method, apply_refund_amount, actual_refund_amount,
            refund_reason, refund_time, use_time, mailing_address,
            channel_product_commission, created_at, updated_at
        FROM order_product_sync 
        WHERE order_no = :order_no
        ORDER BY created_at
        """
        
        products_result = await db.execute(text(products_query), {"order_no": order.order_no})
        products = products_result.fetchall()
        
        # 转换订单数据
        order_data = {
            "order_no": order.order_no,
            "external_no": order.external_no,
            "external_order_status": order.external_order_status,
            "order_type": order.order_type,
            "tenant_id": order.tenant_id,
            "tenant_name": order.tenant_name,
            "customer_id": order.customer_id,
            "create_time": order.create_time.isoformat() if order.create_time else None,
            "pay_type": order.pay_type,
            "pay_time": order.pay_time.isoformat() if order.pay_time else None,
            "arrival_time": order.arrival_time.isoformat() if order.arrival_time else None,
            "pay_status": order.pay_status,
            "order_status": order.order_status,
            "pay_no": order.pay_no,
            "order_amount": float(order.order_amount) if order.order_amount else 0,
            "refund_amount": float(order.refund_amount) if order.refund_amount else 0,
            "settlement_amount": float(order.settlement_amount) if order.settlement_amount else 0,
            "product_count": order.product_count,
            "avg_price": float(order.avg_price) if order.avg_price else 0,
            "channel_fee": float(order.channel_fee) if order.channel_fee else 0,
            "mailing_address": order.mailing_address,
            "mailing_status": order.mailing_status,
            "hotel_confirm_no": order.hotel_confirm_no,
            "sync_status": order.sync_status,
            "sync_time": order.sync_time.isoformat() if order.sync_time else None,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat()
        }
        
        # 转换产品数据
        products_data = []
        for product in products:
            product_data = {
                "id": product.id,
                "external_no": product.external_no,
                "product_id": product.product_id,
                "product_name": product.product_name,
                "categories": {
                    "level1": product.category_level1,
                    "level2": product.category_level2,
                    "level3": product.category_level3,
                    "level4": product.category_level4,
                    "level5": product.category_level5
                },
                "pricing": {
                    "channel_price": float(product.channel_price) if product.channel_price else 0,
                    "channel_commission_rate": float(product.channel_commission_rate) if product.channel_commission_rate else 0,
                    "channel_product_commission": float(product.channel_product_commission) if product.channel_product_commission else 0
                },
                "availability": {
                    "start_time": product.available_start_time.isoformat() if product.available_start_time else None,
                    "end_time": product.available_end_time.isoformat() if product.available_end_time else None
                },
                "channel": {
                    "id": product.channel_id,
                    "name": product.channel_name
                },
                "customer": {
                    "name": product.customer_name,
                    "phone": product.customer_phone,
                    "id_card": product.customer_id_card
                },
                "quantity": product.quantity,
                "status": {
                    "product_status": product.product_status,
                    "refund_status": product.refund_status
                },
                "verification": {
                    "method": product.verify_method,
                    "device": product.verify_device,
                    "device_name": product.verify_device_name
                },
                "refund": {
                    "method": product.refund_method,
                    "apply_amount": float(product.apply_refund_amount) if product.apply_refund_amount else 0,
                    "actual_amount": float(product.actual_refund_amount) if product.actual_refund_amount else 0,
                    "reason": product.refund_reason,
                    "time": product.refund_time.isoformat() if product.refund_time else None
                },
                "use_time": product.use_time.isoformat() if product.use_time else None,
                "mailing_address": product.mailing_address,
                "created_at": product.created_at.isoformat(),
                "updated_at": product.updated_at.isoformat()
            }
            products_data.append(product_data)
        
        return format_response(
            message="获取订单详情成功",
            data={
                "order": order_data,
                "products": products_data
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取订单详情失败: {str(e)}"
        )


@router.get("/products/search", response_model=BaseResponse)
async def search_products(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    order_no: Optional[str] = Query(None, description="订单编号"),
    external_no: Optional[str] = Query(None, description="产品外部编号"),
    product_status: Optional[str] = Query(None, description="产品状态"),
    customer_phone: Optional[str] = Query(None, description="客户手机号"),
    category_level1: Optional[str] = Query(None, description="一级分类"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db)
):
    """通用产品查询接口"""
    try:
        base_query = """
        SELECT 
            ops.id, ops.order_no, ops.external_no, ops.product_name,
            ops.category_level1, ops.category_level4, ops.channel_name,
            ops.quantity, ops.customer_name, ops.customer_phone,
            ops.product_status, ops.verify_method, ops.verify_device_name,
            ops.refund_status, ops.actual_refund_amount, ops.use_time,
            ops.available_start_time, ops.available_end_time,
            ops.created_at, ops.updated_at,
            os.external_no as order_external_no, os.order_status
        FROM order_product_sync ops
        LEFT JOIN order_sync os ON ops.order_no = os.order_no
        WHERE 1=1
        """
        
        count_query = """
        SELECT COUNT(*) 
        FROM order_product_sync ops
        LEFT JOIN order_sync os ON ops.order_no = os.order_no
        WHERE 1=1
        """
        
        conditions = []
        params = {}
        
        if order_no:
            conditions.append("AND ops.order_no ILIKE :order_no")
            params["order_no"] = f"%{order_no}%"
        
        if external_no:
            conditions.append("AND ops.external_no ILIKE :external_no")
            params["external_no"] = f"%{external_no}%"
        
        if product_status:
            conditions.append("AND ops.product_status = :product_status")
            params["product_status"] = product_status
        
        if customer_phone:
            conditions.append("AND ops.customer_phone ILIKE :customer_phone")
            params["customer_phone"] = f"%{customer_phone}%"
        
        if category_level1:
            conditions.append("AND ops.category_level1 = :category_level1")
            params["category_level1"] = category_level1
        
        if start_date:
            conditions.append("AND ops.created_at >= :start_date")
            params["start_date"] = start_date
        
        if end_date:
            conditions.append("AND ops.created_at <= :end_date")
            params["end_date"] = end_date
        
        where_clause = " ".join(conditions)
        full_query = base_query + where_clause + " ORDER BY ops.created_at DESC LIMIT :limit OFFSET :offset"
        full_count_query = count_query + where_clause
        
        params["limit"] = page_size
        params["offset"] = (page - 1) * page_size
        
        # 执行查询
        count_result = await db.execute(text(full_count_query), params)
        total = count_result.scalar()
        
        result = await db.execute(text(full_query), params)
        products = result.fetchall()
        
        # 转换数据格式
        product_list = []
        for product in products:
            product_dict = {
                "id": product.id,
                "order_no": product.order_no,
                "order_external_no": product.order_external_no,
                "order_status": product.order_status,
                "external_no": product.external_no,
                "product_name": product.product_name,
                "category_level1": product.category_level1,
                "category_level4": product.category_level4,
                "channel_name": product.channel_name,
                "quantity": product.quantity,
                "customer_name": product.customer_name,
                "customer_phone": product.customer_phone,
                "product_status": product.product_status,
                "verify_method": product.verify_method,
                "verify_device_name": product.verify_device_name,
                "refund_status": product.refund_status,
                "refund_amount": float(product.actual_refund_amount) if product.actual_refund_amount else 0,
                "use_time": product.use_time.isoformat() if product.use_time else None,
                "available_start_time": product.available_start_time.isoformat() if product.available_start_time else None,
                "available_end_time": product.available_end_time.isoformat() if product.available_end_time else None,
                "created_at": product.created_at.isoformat(),
                "updated_at": product.updated_at.isoformat()
            }
            product_list.append(product_dict)
        
        return format_response(
            message="查询产品成功",
            data={
                "products": product_list,
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
            detail=f"查询产品失败: {str(e)}"
        )


@router.get("/statistics/dashboard", response_model=BaseResponse)
async def get_dashboard_statistics(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    tenant_id: Optional[str] = Query(None, description="租户ID"),
    db: AsyncSession = Depends(get_db)
):
    """获取仪表板统计数据"""
    try:
        # 构建基础条件
        conditions = ["1=1"]
        params = {}
        
        if start_date:
            conditions.append("create_time >= :start_date")
            params["start_date"] = start_date
        
        if end_date:
            conditions.append("create_time <= :end_date")
            params["end_date"] = end_date
        
        if tenant_id:
            conditions.append("tenant_id = :tenant_id")
            params["tenant_id"] = tenant_id
        
        where_clause = " AND ".join(conditions)
        
        # 订单统计
        order_stats_query = f"""
        SELECT 
            COUNT(*) as total_orders,
            COUNT(CASE WHEN order_status = 'COMPT' THEN 1 END) as completed_orders,
            COUNT(CASE WHEN order_status = 'REFD' THEN 1 END) as refunded_orders,
            COUNT(CASE WHEN pay_status = 'PAID' THEN 1 END) as paid_orders,
            COALESCE(SUM(order_amount), 0) as total_amount,
            COALESCE(SUM(refund_amount), 0) as total_refund,
            COALESCE(SUM(settlement_amount), 0) as total_settlement
        FROM order_sync 
        WHERE {where_clause}
        """
        
        order_result = await db.execute(text(order_stats_query), params)
        order_stats = order_result.fetchone()
        
        # 产品统计
        product_stats_query = f"""
        SELECT 
            COUNT(*) as total_products,
            COUNT(CASE WHEN ops.product_status = 'COMPT' THEN 1 END) as used_products,
            COUNT(CASE WHEN ops.refund_status = '已退款' THEN 1 END) as refunded_products
        FROM order_product_sync ops
        JOIN order_sync os ON ops.order_no = os.order_no
        WHERE {where_clause}
        """
        
        product_result = await db.execute(text(product_stats_query), params)
        product_stats = product_result.fetchone()
        
        # 按状态分组统计
        status_stats_query = f"""
        SELECT 
            order_status,
            COUNT(*) as count,
            COALESCE(SUM(order_amount), 0) as amount
        FROM order_sync 
        WHERE {where_clause}
        GROUP BY order_status
        ORDER BY count DESC
        """
        
        status_result = await db.execute(text(status_stats_query), params)
        status_stats = status_result.fetchall()
        
        # 按日期统计（最近7天）
        daily_stats_query = f"""
        SELECT 
            DATE(create_time) as date,
            COUNT(*) as orders,
            COALESCE(SUM(order_amount), 0) as amount
        FROM order_sync 
        WHERE {where_clause} AND create_time >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY DATE(create_time)
        ORDER BY date DESC
        """
        
        daily_result = await db.execute(text(daily_stats_query), params)
        daily_stats = daily_result.fetchall()
        
        return format_response(
            message="获取仪表板统计成功",
            data={
                "summary": {
                    "total_orders": order_stats.total_orders,
                    "completed_orders": order_stats.completed_orders,
                    "refunded_orders": order_stats.refunded_orders,
                    "paid_orders": order_stats.paid_orders,
                    "total_amount": float(order_stats.total_amount),
                    "total_refund": float(order_stats.total_refund),
                    "total_settlement": float(order_stats.total_settlement),
                    "total_products": product_stats.total_products,
                    "used_products": product_stats.used_products,
                    "refunded_products": product_stats.refunded_products
                },
                "status_distribution": [
                    {
                        "status": stat.order_status,
                        "count": stat.count,
                        "amount": float(stat.amount)
                    }
                    for stat in status_stats
                ],
                "daily_trends": [
                    {
                        "date": stat.date.isoformat(),
                        "orders": stat.orders,
                        "amount": float(stat.amount)
                    }
                    for stat in daily_stats
                ]
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取仪表板统计失败: {str(e)}"
        )