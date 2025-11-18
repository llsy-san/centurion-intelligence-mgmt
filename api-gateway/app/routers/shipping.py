"""
API网关 - 发货服务路由
定义具体的发货相关API接口，转发到后端发货服务
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


async def forward_to_shipping_service(method: str, path: str, json_data=None, params=None):
    """转发请求到发货服务"""
    try:
        async with httpx.AsyncClient() as client:
            url = f"{config.shipping_service_url}{path}"
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
            detail="发货服务不可用"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发货服务请求失败: {str(e)}"
        )


@router.post("/shipping", response_model=BaseResponse, summary="创建发货单")
async def create_shipping(
    shipping_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    创建发货单
    
    - **shipping_data**: 发货数据，包含订单ID、收货地址等
    """
    return await forward_to_shipping_service("POST", "/", json_data=shipping_data)


@router.get("/shipping/{shipping_id}", response_model=BaseResponse, summary="获取发货详情")
async def get_shipping(
    shipping_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    根据发货ID获取发货详情
    
    - **shipping_id**: 发货ID
    """
    return await forward_to_shipping_service("GET", f"/{shipping_id}")


@router.get("/shipping/order/{order_id}", response_model=BaseResponse, summary="获取订单发货信息")
async def get_shipping_by_order(
    order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    根据订单ID获取发货信息
    
    - **order_id**: 订单ID
    """
    return await forward_to_shipping_service("GET", f"/order/{order_id}")


@router.put("/shipping/{shipping_id}/status", response_model=BaseResponse, summary="更新发货状态")
async def update_shipping_status(
    shipping_id: str,
    status_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    更新发货状态
    
    - **shipping_id**: 发货ID
    - **status_data**: 状态数据，包含新的发货状态
    """
    return await forward_to_shipping_service("PUT", f"/{shipping_id}/status", json_data=status_data)


@router.get("/shipping/{shipping_id}/track", response_model=BaseResponse, summary="物流追踪")
async def track_shipping(
    shipping_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    物流追踪查询
    
    - **shipping_id**: 发货ID
    """
    return await forward_to_shipping_service("GET", f"/{shipping_id}/track")


@router.post("/shipping/{shipping_id}/deliver", response_model=BaseResponse, summary="确认发货")
async def confirm_delivery(
    shipping_id: str,
    delivery_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    确认发货
    
    - **shipping_id**: 发货ID
    - **delivery_data**: 发货数据，包含物流公司、运单号等
    """
    return await forward_to_shipping_service("POST", f"/{shipping_id}/deliver", json_data=delivery_data)


@router.get("/shipping", response_model=BaseResponse, summary="获取发货列表")
async def list_shipping(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的记录数"),
    status: Optional[str] = Query(None, description="发货状态筛选"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取发货列表（管理员功能）
    
    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数
    - **status**: 发货状态筛选（可选）
    """
    params = {"skip": skip, "limit": limit}
    if status:
        params["status"] = status
    return await forward_to_shipping_service("GET", "/", params=params)