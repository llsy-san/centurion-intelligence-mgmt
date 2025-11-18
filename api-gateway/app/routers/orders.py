"""
API网关 - 订单服务路由
定义具体的订单相关API接口，转发到后端订单服务
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import httpx

from ..config import config
from ..models import BaseResponse
from ..utils import format_response

router = APIRouter()
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户（JWT认证）"""
    # 暂时跳过JWT验证，返回模拟用户
    return {"user_id": "test", "username": "test_user"}


async def forward_to_order_service(method: str, path: str, json_data=None, params=None):
    """转发请求到订单服务"""
    try:
        async with httpx.AsyncClient() as client:
            url = f"{config.order_service_url}{path}"
            response = await client.request(
                method=method,
                url=url,
                json=json_data,
                params=params,
                timeout=30.0
            )
            return response.json()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="订单服务不可用"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"订单服务请求失败: {str(e)}"
        )


@router.post("/orders", response_model=BaseResponse, summary="创建订单")
async def create_order(
    order_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    创建新订单
    
    - **order_data**: 订单数据
    """
    return await forward_to_order_service("POST", "/", json_data=order_data)


@router.get("/orders/{order_id}", response_model=BaseResponse, summary="获取订单详情")
async def get_order(
    order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    根据订单ID获取订单详情
    
    - **order_id**: 订单ID
    """
    return await forward_to_order_service("GET", f"/{order_id}")


@router.get("/orders/user/{user_id}", response_model=BaseResponse, summary="获取用户订单列表")
async def get_user_orders(
    user_id: str,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的记录数"),
    current_user: dict = Depends(get_current_user)
):
    """
    根据用户ID获取订单列表
    
    - **user_id**: 用户ID
    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数
    """
    params = {"skip": skip, "limit": limit}
    return await forward_to_order_service("GET", f"/user/{user_id}", params=params)


@router.put("/orders/{order_id}/status", response_model=BaseResponse, summary="更新订单状态")
async def update_order_status(
    order_id: str,
    status_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    更新订单状态
    
    - **order_id**: 订单ID
    - **status_data**: 状态数据，包含新的订单状态
    """
    return await forward_to_order_service("PUT", f"/{order_id}/status", json_data=status_data)


@router.put("/orders/{order_id}/cancel", response_model=BaseResponse, summary="取消订单")
async def cancel_order(
    order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    取消订单
    
    - **order_id**: 订单ID
    """
    return await forward_to_order_service("PUT", f"/{order_id}/cancel")


@router.get("/orders", response_model=BaseResponse, summary="获取订单列表")
async def list_orders(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的记录数"),
    status: Optional[str] = Query(None, description="订单状态筛选"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取订单列表（管理员功能）
    
    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数
    - **status**: 订单状态筛选（可选）
    """
    params = {"skip": skip, "limit": limit}
    if status:
        params["status"] = status
    return await forward_to_order_service("GET", "/", params=params)