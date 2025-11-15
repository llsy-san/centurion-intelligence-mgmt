"""
定时任务调度器
使用APScheduler管理定时任务
"""
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))
from utils import setup_logging

from .services.sync_service import sync_service

logger = setup_logging("scheduler")

# 全局调度器实例
scheduler = None


async def sync_orders_job():
    """同步订单数据的定时任务"""
    try:
        logger.info("开始执行订单同步定时任务")
        
        # 同步最近24小时的数据
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        
        result = await sync_service.sync_orders(start_time, end_time)
        
        logger.info(f"订单同步定时任务完成: {result}")
        
    except Exception as e:
        logger.error(f"订单同步定时任务执行失败: {str(e)}")


async def sync_full_orders_job():
    """全量同步订单数据的定时任务（每周执行）"""
    try:
        logger.info("开始执行全量订单同步定时任务")
        
        # 同步最近7天的数据
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        
        result = await sync_service.sync_orders(start_time, end_time)
        
        logger.info(f"全量订单同步定时任务完成: {result}")
        
    except Exception as e:
        logger.error(f"全量订单同步定时任务执行失败: {str(e)}")


async def start_scheduler():
    """启动定时任务调度器"""
    global scheduler
    
    try:
        scheduler = AsyncIOScheduler()
        
        # 添加订单同步任务 - 每小时执行一次
        scheduler.add_job(
            sync_orders_job,
            CronTrigger(minute=0),  # 每小时的0分执行
            id="sync_orders_hourly",
            name="同步订单数据（每小时）",
            replace_existing=True
        )
        
        # 添加全量同步任务 - 每天凌晨2点执行
        scheduler.add_job(
            sync_full_orders_job,
            CronTrigger(hour=2, minute=0),  # 每天凌晨2点执行
            id="sync_full_orders_daily",
            name="全量同步订单数据（每天）",
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("定时任务调度器启动成功")
        
        # 立即执行一次同步任务（可选）
        # await sync_orders_job()
        
    except Exception as e:
        logger.error(f"启动定时任务调度器失败: {str(e)}")
        raise


async def stop_scheduler():
    """停止定时任务调度器"""
    global scheduler
    
    if scheduler:
        try:
            scheduler.shutdown(wait=True)
            logger.info("定时任务调度器已停止")
        except Exception as e:
            logger.error(f"停止定时任务调度器失败: {str(e)}")


def get_scheduler_status():
    """获取调度器状态"""
    global scheduler
    
    if not scheduler:
        return {"status": "stopped", "jobs": []}
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    return {
        "status": "running" if scheduler.running else "stopped",
        "jobs": jobs
    }