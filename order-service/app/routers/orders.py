"""
订单服务路由
定义订单相关的API接口
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Order, OrderCreate, OrderStatus, BaseResponse
from ..utils import format_response
from ..database import get_db
from ..services import OrderService

router = APIRouter()


@router.post("/", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
        order_data: OrderCreate,
        db: AsyncSession = Depends(get_db)
):
    """创建订单"""
    try:
        order_service = OrderService(db)
        order = await order_service.create_order(order_data)

        return format_response(
            message="订单创建成功",
            data=order.dict()
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="订单创建失败"
        )


@router.get("/{order_id}", response_model=BaseResponse)
async def get_order(
        order_id: str,
        db: AsyncSession = Depends(get_db)
):
    """根据ID获取订单详情"""
    try:
        order_service = OrderService(db)
        order = await order_service.get_order(order_id)

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订单不存在"
            )

        return format_response(
            message="获取订单成功",
            data=order.dict()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取订单失败"
        )


@router.get("/user/{user_id}", response_model=BaseResponse)
async def get_user_orders(
        user_id: str,
        skip: int = Query(0, ge=0, description="跳过的记录数"),
        limit: int = Query(10, ge=1, le=100, description="返回的记录数"),
        db: AsyncSession = Depends(get_db)
):
    """根据用户ID获取订单列表"""
    try:
        order_service = OrderService(db)
        orders = await order_service.get_orders_by_user(user_id, skip, limit)

        return format_response(
            message="获取用户订单列表成功",
            data={
                "orders": [order.dict() for order in orders],
                "total": len(orders),
                "skip": skip,
                "limit": limit
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户订单列表失败"
        )


@router.put("/{order_id}/status", response_model=BaseResponse)
async def update_order_status(
        order_id: str,
        status: OrderStatus,
        db: AsyncSession = Depends(get_db)
):
    """更新订单状态"""
    try:
        order_service = OrderService(db)
        success = await order_service.update_order_status(order_id, status)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订单不存在"
            )

        return format_response(message="订单状态更新成功")

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="订单状态更新失败"
        )


@router.put("/{order_id}/cancel", response_model=BaseResponse)
async def cancel_order(
        order_id: str,
        db: AsyncSession = Depends(get_db)
):
    """取消订单"""
    try:
        order_service = OrderService(db)
        success = await order_service.cancel_order(order_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订单不存在"
            )

        return format_response(message="订单取消成功")

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="订单取消失败"
        )
