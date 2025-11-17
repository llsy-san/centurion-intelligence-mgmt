"""
用户资产管理路由
专门处理门票二维码和用户资产相关的API接口
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from ..models import UserAsset, AssetType, BaseResponse
from ..utils import format_response
from ..database import get_db
from ..services import UserAssetService

router = APIRouter()


@router.get("/user/{user_id}", response_model=BaseResponse)
async def get_user_assets(
    user_id: str,
    asset_type: Optional[AssetType] = Query(None, description="资产类型筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """获取用户资产列表"""
    try:
        asset_service = UserAssetService(db)
        assets = await asset_service.get_user_assets(user_id, asset_type)
        
        # 简单分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_assets = assets[start:end]
        
        return format_response(
            message="获取用户资产成功",
            data={
                "assets": [asset.dict() for asset in paginated_assets],
                "total": len(assets),
                "page": page,
                "page_size": page_size,
                "total_pages": (len(assets) + page_size - 1) // page_size
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户资产失败"
        )


@router.get("/code/{asset_code}", response_model=BaseResponse)
async def get_asset_by_code(
    asset_code: str,
    db: AsyncSession = Depends(get_db)
):
    """根据资产编码获取资产详情（用于二维码扫描）"""
    try:
        asset_service = UserAssetService(db)
        asset = await asset_service.get_asset_by_code(asset_code)
        
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="资产不存在或二维码无效"
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


@router.post("/{asset_id}/use", response_model=BaseResponse)
async def use_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """使用资产（如验票入园）"""
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


@router.get("/{asset_id}", response_model=BaseResponse)
async def get_asset_detail(
    asset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取特定资产详情"""
    try:
        asset_service = UserAssetService(db)
        
        # 通过ID查询（需要在service中添加此方法）
        from sqlalchemy import select
        from ..database import UserAssetModel
        
        result = await db.execute(
            select(UserAssetModel).where(UserAssetModel.id == asset_id)
        )
        db_asset = result.scalar_one_or_none()
        
        if not db_asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="资产不存在"
            )
        
        asset = asset_service._db_to_model(db_asset)
        
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


@router.get("/tickets/user/{user_id}", response_model=BaseResponse)
async def get_user_tickets(
    user_id: str,
    status_filter: Optional[str] = Query(None, description="状态筛选: active, used, expired"),
    scenic_area_id: Optional[str] = Query(None, description="景区ID筛选"),
    db: AsyncSession = Depends(get_db)
):
    """获取用户门票列表（专门的门票查询接口）"""
    try:
        asset_service = UserAssetService(db)
        assets = await asset_service.get_user_assets(user_id, AssetType.TICKET)
        
        # 筛选门票
        tickets = []
        for asset in assets:
            # 状态筛选
            if status_filter and asset.status.value != status_filter:
                continue
            
            # 景区筛选
            if scenic_area_id and asset.metadata and asset.metadata.get("scenic_area_id") != scenic_area_id:
                continue
            
            tickets.append(asset)
        
        return format_response(
            message="获取用户门票成功",
            data={
                "tickets": [ticket.dict() for ticket in tickets],
                "total": len(tickets)
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户门票失败"
        )


@router.post("/tickets/{ticket_id}/validate", response_model=BaseResponse)
async def validate_ticket(
    ticket_id: str,
    validation_data: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
):
    """验证门票有效性（景区入园验证）"""
    try:
        asset_service = UserAssetService(db)
        
        # 获取门票信息
        from sqlalchemy import select
        from ..database import UserAssetModel
        from datetime import datetime
        
        result = await db.execute(
            select(UserAssetModel).where(UserAssetModel.id == ticket_id)
        )
        db_asset = result.scalar_one_or_none()
        
        if not db_asset:
            return format_response(
                success=False,
                message="门票不存在",
                error_code="TICKET_NOT_FOUND"
            )
        
        asset = asset_service._db_to_model(db_asset)
        
        # 检查门票状态
        if asset.status.value != "active":
            return format_response(
                success=False,
                message=f"门票状态无效: {asset.status.value}",
                error_code="TICKET_INVALID_STATUS"
            )
        
        # 检查有效期
        now = datetime.now()
        if asset.valid_until and now > asset.valid_until:
            return format_response(
                success=False,
                message="门票已过期",
                error_code="TICKET_EXPIRED"
            )
        
        if asset.valid_from and now < asset.valid_from:
            return format_response(
                success=False,
                message="门票尚未生效",
                error_code="TICKET_NOT_ACTIVE"
            )
        
        return format_response(
            message="门票验证通过",
            data={
                "ticket_id": ticket_id,
                "ticket_name": asset.asset_name,
                "scenic_area": asset.metadata.get("scenic_area_name") if asset.metadata else None,
                "ticket_type": asset.metadata.get("ticket_type") if asset.metadata else None,
                "valid_until": asset.valid_until.isoformat() if asset.valid_until else None,
                "can_use": True
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"门票验证失败: {str(e)}"
        )