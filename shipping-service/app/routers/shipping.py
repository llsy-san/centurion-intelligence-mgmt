"""
发货服务路由
定义发货相关的API接口 - 支持门票二维码和用户资产管理
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional

from ..models import (
    Shipping, ShippingCreate, ShippingStatus, BaseResponse,
    ThirdPartyShippingRequest, ThirdPartyShippingResponse,
    UserAsset, AssetType, OrderItem
)
from ..utils import format_response
from ..database import get_db
from ..services import ShippingService, UserAssetService

router = APIRouter()


@router.post("/", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_shipping(
    shipping_data: ShippingCreate,
    order_items: List[OrderItem] = [],
    user_id: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    """创建发货记录"""
    try:
        shipping_service = ShippingService(db)
        shipping = await shipping_service.create_shipping(shipping_data, order_items)
        
        # 异步处理发货（生成二维码或调用第三方系统）
        background_tasks.add_task(
            shipping_service.process_shipping, 
            shipping.id, 
            order_items or [],
            user_id or ""
        )
        
        return format_response(
            message="发货记录创建成功，正在处理发货",
            data=shipping.dict()
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发货记录创建失败"
        )


@router.get("/{shipping_id}", response_model=BaseResponse)
async def get_shipping(
    shipping_id: str,
    sync_status: bool = Query(False, description="是否同步第三方状态"),
    db: AsyncSession = Depends(get_db)
):
    """根据ID获取发货详情"""
    try:
        shipping_service = ShippingService(db)
        shipping = await shipping_service.get_shipping(shipping_id)
        
        if not shipping:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="发货记录不存在"
            )
        
        return format_response(
            message="获取发货记录成功",
            data=shipping.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取发货记录失败"
        )


@router.get("/order/{order_id}", response_model=BaseResponse)
async def get_shipping_by_order(
    order_id: str,
    db: AsyncSession = Depends(get_db)
):
    """根据订单ID获取发货详情"""
    try:
        shipping_service = ShippingService(db)
        shipping = await shipping_service.get_shipping_by_order(order_id)
        
        if not shipping:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="发货记录不存在"
            )
        
        return format_response(
            message="获取发货记录成功",
            data=shipping.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取发货记录失败"
        )


@router.post("/{shipping_id}/process", response_model=BaseResponse)
async def process_shipping(
    shipping_id: str,
    order_items: Optional[List[OrderItem]] = None,
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """手动处理发货"""
    try:
        shipping_service = ShippingService(db)
        success = await shipping_service.process_shipping(shipping_id, order_items or [], user_id or "")
        
        if success:
            return format_response(message="发货处理成功")
        else:
            return format_response(
                success=False,
                message="发货处理失败",
                error_code="SHIPPING_FAILED"
            )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发货处理失败: {str(e)}"
        )


@router.post("/{shipping_id}/cancel", response_model=BaseResponse)
async def cancel_shipping(
    shipping_id: str,
    db: AsyncSession = Depends(get_db)
):
    """取消发货"""
    try:
        shipping_service = ShippingService(db)
        success = await shipping_service.cancel_shipping(shipping_id)
        
        if success:
            return format_response(message="发货取消成功")
        else:
            return format_response(
                success=False,
                message="发货取消失败",
                error_code="CANCEL_SHIPPING_FAILED"
            )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发货取消失败: {str(e)}"
        )


# 用户资产相关接口
@router.get("/assets/user/{user_id}", response_model=BaseResponse)
async def get_user_assets(
    user_id: str,
    asset_type: Optional[AssetType] = Query(None, description="资产类型筛选"),
    db: AsyncSession = Depends(get_db)
):
    """获取用户资产列表"""
    try:
        asset_service = UserAssetService(db)
        assets = await asset_service.get_user_assets(user_id, asset_type)
        
        return format_response(
            message="获取用户资产成功",
            data={
                "assets": [asset.dict() for asset in assets],
                "total": len(assets)
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户资产失败"
        )


@router.get("/assets/code/{asset_code}", response_model=BaseResponse)
async def get_asset_by_code(
    asset_code: str,
    db: AsyncSession = Depends(get_db)
):
    """根据资产编码获取资产详情"""
    try:
        asset_service = UserAssetService(db)
        asset = await asset_service.get_asset_by_code(asset_code)
        
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="资产不存在"
            )
        
        return format_response(
            message="获取资产详情成功",
            data=asset.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取资产详情失败"
        )


@router.post("/assets/{asset_id}/use", response_model=BaseResponse)
async def use_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """使用资产（如验票）"""
    try:
        asset_service = UserAssetService(db)
        success = await asset_service.use_asset(asset_id)
        
        if success:
            return format_response(message="资产使用成功")
        else:
            return format_response(
                success=False,
                message="资产使用失败，可能已被使用或不存在",
                error_code="ASSET_USE_FAILED"
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"资产使用失败: {str(e)}"
        )


@router.put("/{shipping_id}/status", response_model=BaseResponse)
async def update_shipping_status(
    shipping_id: str,
    status: ShippingStatus,
    tracking_number: Optional[str] = None,
    carrier: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """手动更新发货状态"""
    try:
        shipping_service = ShippingService(db)
        success = await shipping_service.update_shipping_status(
            shipping_id, status, tracking_number, carrier
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="发货记录不存在"
            )
        
        return format_response(message="发货状态更新成功")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发货状态更新失败"
        )