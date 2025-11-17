"""
Celery 任务管理路由
提供类似 XXL-JOB 的管理界面 API
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from ..models import BaseResponse
from ..utils import format_response
from ..celery.celery_app import celery_app
from ..celery import celery_tasks

router = APIRouter()


class TaskRequest(BaseModel):
    """任务请求模型"""
    task_name: str
    params: Optional[Dict[str, Any]] = {}
    queue: Optional[str] = "default"


class TaskResponse(BaseModel):
    """任务响应模型"""
    task_id: str
    task_name: str
    status: str
    created_at: datetime


@router.get("/status", response_model=BaseResponse)
async def get_celery_status():
    """获取 Celery 状态信息"""
    try:
        # 获取活跃任务
        active_tasks = celery_app.control.inspect().active()
        
        # 获取注册任务
        registered_tasks = celery_app.control.inspect().registered()
        
        # 获取队列信息
        stats = celery_app.control.inspect().stats()
        
        return format_response(
            message="获取 Celery 状态成功",
            data={
                "active_tasks": active_tasks,
                "registered_tasks": registered_tasks,
                "worker_stats": stats,
                "beat_schedule": {
                    name: {
                        "task": schedule["task"],
                        "schedule": str(schedule["schedule"]),
                        "options": schedule.get("options", {})
                    }
                    for name, schedule in celery_app.conf.beat_schedule.items()
                }
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取 Celery 状态失败: {str(e)}"
        )


@router.post("/jobs/sync-orders", response_model=BaseResponse)
async def trigger_sync_orders(hours: int = 24):
    """手动触发订单同步任务"""
    try:
        task_result = celery_tasks.sync_orders.delay(hours=hours)
        
        return format_response(
            message="订单同步任务已提交",
            data={
                "task_id": task_result.id,
                "task_name": "sync_orders",
                "status": "PENDING",
                "params": {"hours": hours}
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"触发订单同步任务失败: {str(e)}"
        )


@router.post("/jobs/sync-full-orders", response_model=BaseResponse)
async def trigger_sync_full_orders(days: int = 7):
    """手动触发全量订单同步任务"""
    try:
        task_result = celery_tasks.sync_full_orders.delay(days=days)
        
        return format_response(
            message="全量订单同步任务已提交",
            data={
                "task_id": task_result.id,
                "task_name": "sync_full_orders",
                "status": "PENDING",
                "params": {"days": days}
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"触发全量订单同步任务失败: {str(e)}"
        )


@router.post("/jobs/data-analysis", response_model=BaseResponse)
async def trigger_data_analysis():
    """手动触发数据分析任务"""
    try:
        task_result = celery_tasks.data_analysis.delay()
        
        return format_response(
            message="数据分析任务已提交",
            data={
                "task_id": task_result.id,
                "task_name": "data_analysis",
                "status": "PENDING"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"触发数据分析任务失败: {str(e)}"
        )


@router.post("/jobs/custom", response_model=BaseResponse)
async def trigger_custom_task(request: TaskRequest):
    """触发自定义任务"""
    try:
        task_result = celery_tasks.custom_task.delay(
            task_name=request.task_name,
            params=request.params
        )
        
        return format_response(
            message=f"自定义任务 {request.task_name} 已提交",
            data={
                "task_id": task_result.id,
                "task_name": request.task_name,
                "status": "PENDING",
                "params": request.params
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"触发自定义任务失败: {str(e)}"
        )


@router.get("/jobs/{task_id}/status", response_model=BaseResponse)
async def get_task_status(task_id: str):
    """获取任务执行状态"""
    try:
        task_result = celery_app.AsyncResult(task_id)
        
        response_data = {
            "task_id": task_id,
            "status": task_result.status,
            "result": task_result.result,
        }
        
        if task_result.status == 'PROGRESS':
            response_data["meta"] = task_result.info
        elif task_result.status == 'FAILURE':
            response_data["error"] = str(task_result.info)
        
        return format_response(
            message="获取任务状态成功",
            data=response_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务状态失败: {str(e)}"
        )


@router.post("/jobs/{task_id}/cancel", response_model=BaseResponse)
async def cancel_task(task_id: str):
    """取消任务"""
    try:
        celery_app.control.revoke(task_id, terminate=True)
        
        return format_response(
            message="任务取消请求已发送",
            data={"task_id": task_id, "action": "cancelled"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消任务失败: {str(e)}"
        )


@router.get("/workers", response_model=BaseResponse)
async def get_workers():
    """获取工作节点信息"""
    try:
        stats = celery_app.control.inspect().stats()
        active = celery_app.control.inspect().active()
        
        workers_info = []
        if stats:
            for worker_name, worker_stats in stats.items():
                worker_info = {
                    "name": worker_name,
                    "status": "online",
                    "active_tasks": len(active.get(worker_name, [])) if active else 0,
                    "processed_tasks": worker_stats.get("total", {}),
                    "pool_info": worker_stats.get("pool", {}),
                    "rusage": worker_stats.get("rusage", {})
                }
                workers_info.append(worker_info)
        
        return format_response(
            message="获取工作节点信息成功",
            data={"workers": workers_info, "total_workers": len(workers_info)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工作节点信息失败: {str(e)}"
        )


@router.get("/queues", response_model=BaseResponse)
async def get_queues():
    """获取队列信息"""
    try:
        # 获取活跃队列
        active_queues = celery_app.control.inspect().active_queues()
        
        return format_response(
            message="获取队列信息成功",
            data={
                "queues": active_queues,
                "configured_queues": ["sync_queue", "analysis_queue", "default"]
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取队列信息失败: {str(e)}"
        )