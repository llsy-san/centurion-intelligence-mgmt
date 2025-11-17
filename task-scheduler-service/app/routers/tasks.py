"""
定时任务管理路由
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any

from ..models import BaseResponse
from ..utils import format_response
from ..scheduler import get_scheduler_status, sync_orders_job, sync_full_orders_job
from ..services.sync_service import sync_service

router = APIRouter()


@router.get("/status", response_model=BaseResponse)
async def get_task_status():
    """获取定时任务状态"""
    try:
        scheduler_status = get_scheduler_status()
        sync_logs = await sync_service.get_sync_status(limit=5)
        
        return format_response(
            message="获取任务状态成功",
            data={
                "scheduler": scheduler_status,                                  # 调度器状态信息
                "recent_sync_logs": sync_logs                                   # 最近同步日志
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务状态失败: {str(e)}"
        )


@router.post("/sync/orders/manual", response_model=BaseResponse)
async def manual_sync_orders():
    """手动触发订单同步"""
    try:
        await sync_orders_job()
        return format_response(message="手动同步订单任务已触发")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"手动同步失败: {str(e)}"
        )


@router.post("/sync/orders/full", response_model=BaseResponse)
async def manual_full_sync_orders():
    """手动触发全量订单同步"""
    try:
        await sync_full_orders_job()
        return format_response(message="手动全量同步订单任务已触发")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"手动全量同步失败: {str(e)}"
        )


@router.get("/logs", response_model=BaseResponse)
async def get_sync_logs(limit: int = 20):
    """获取同步日志"""
    try:
        logs = await sync_service.get_sync_status(limit=limit)
        return format_response(
            message="获取同步日志成功",
            data=logs
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取同步日志失败: {str(e)}"
        )