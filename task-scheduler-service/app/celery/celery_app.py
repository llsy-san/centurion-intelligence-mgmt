"""
Celery 任务队列集成
提供分布式任务调度能力
"""
from celery import Celery
from celery.schedules import crontab

from ..config import config

# 创建Celery实例
celery_app = Celery(
    'centurion-task-scheduler',
    broker=config.redis_url,
    backend=config.redis_url,
    include=['app.celery.celery_tasks']  # 包含任务模块
)

# Celery配置
celery_app.conf.update(
    # 时区设置
    timezone='Asia/Shanghai',
    enable_utc=True,
    
    # 任务序列化
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # 任务结果过期时间
    result_expires=3600,
    
    # 任务路由
    task_routes={
        'app.celery.celery_tasks.sync_orders': {'queue': 'sync_queue'},
        'app.celery.celery_tasks.sync_full_orders': {'queue': 'sync_queue'},
        'app.celery.celery_tasks.data_analysis': {'queue': 'analysis_queue'},
    },
    
    # 定时任务配置
    beat_schedule={
        'sync-orders-hourly': {
            'task': 'app.celery.celery_tasks.sync_orders',
            'schedule': crontab(minute='0'),  # 每小时执行
            'options': {'queue': 'sync_queue'}
        },
        'sync-full-orders-daily': {
            'task': 'app.celery.celery_tasks.sync_full_orders',
            'schedule': crontab(hour='2', minute='0'),  # 每天凌晨2点
            'options': {'queue': 'sync_queue'}
        },
        'data-analysis-daily': {
            'task': 'app.celery.celery_tasks.data_analysis',
            'schedule': crontab(hour='3', minute='0'),  # 每天凌晨3点
            'options': {'queue': 'analysis_queue'}
        },
    }
)

if __name__ == '__main__':
    celery_app.start()