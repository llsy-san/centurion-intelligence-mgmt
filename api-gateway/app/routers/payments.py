"""
API网关 - 支付服务路由
定义具体的支付相关API接口，转发到后端支付服务
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


async def forward_to_payment_service(method: str, path: str, json_data=None, params=None):
    """转发请求到支付服务"""
    try:
        async with httpx.AsyncClient() as client:
            url = f"{config.payment_service_url}{path}"
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
            detail="支付服务不可用"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"支付服务请求失败: {str(e)}"
        )


@router.post("/payments", response_model=BaseResponse, summary="创建支付")
async def create_payment(
    payment_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    创建支付订单
    
    - **payment_data**: 支付数据，包含订单ID、支付方式等
    """
    return await forward_to_payment_service("POST", "/", json_data=payment_data)


@router.get("/payments/{payment_id}", response_model=BaseResponse, summary="获取支付详情")
async def get_payment(
    payment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    根据支付ID获取支付详情
    
    - **payment_id**: 支付ID
    """
    return await forward_to_payment_service("GET", f"/{payment_id}")


@router.get("/payments/order/{order_id}", response_model=BaseResponse, summary="获取订单支付信息")
async def get_payment_by_order(
    order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    根据订单ID获取支付信息
    
    - **order_id**: 订单ID
    """
    return await forward_to_payment_service("GET", f"/order/{order_id}")


@router.post("/payments/{payment_id}/process", response_model=BaseResponse, summary="处理支付")
async def process_payment(
    payment_id: str,
    payment_method_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    处理支付
    
    - **payment_id**: 支付ID
    - **payment_method_data**: 支付方式数据
    """
    return await forward_to_payment_service("POST", f"/{payment_id}/process", json_data=payment_method_data)


@router.post("/payments/{payment_id}/refund", response_model=BaseResponse, summary="退款")
async def refund_payment(
    payment_id: str,
    refund_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    申请退款
    
    - **payment_id**: 支付ID
    - **refund_data**: 退款数据，包含退款金额、原因等
    """
    return await forward_to_payment_service("POST", f"/{payment_id}/refund", json_data=refund_data)


@router.get("/payments/{payment_id}/status", response_model=BaseResponse, summary="查询支付状态")
async def get_payment_status(
    payment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    查询支付状态
    
    - **payment_id**: 支付ID
    """
    return await forward_to_payment_service("GET", f"/{payment_id}/status")


@router.get("/payments", response_model=BaseResponse, summary="获取支付列表")
async def list_payments(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的记录数"),
    status: Optional[str] = Query(None, description="支付状态筛选"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取支付列表（管理员功能）
    
    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数
    - **status**: 支付状态筛选（可选）
    """
    params = {"skip": skip, "limit": limit}
    if status:
        params["status"] = status
    return await forward_to_payment_service("GET", "/", params=params)