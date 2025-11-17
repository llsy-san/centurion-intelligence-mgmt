"""
Celery 配置文件
"""
from celery.schedules import crontab

# Celery 配置
CELERY_CONFIG = {
    # 基础配置
    'timezone': 'Asia/Shanghai',
    'enable_utc': True,
    
    # 序列化配置
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    
    # 结果后端配置
    'result_expires': 3600,  # 结果过期时间（秒）
    'result_backend_transport_options': {
        'master_name': 'mymaster',
    },
    
    # 任务配置
    'task_acks_late': True,  # 任务确认晚于执行
    'task_reject_on_worker_lost': True,  # Worker丢失时拒绝任务
    'task_time_limit': 300,  # 任务超时时间（秒）
    'task_soft_time_limit': 240,  # 任务软超时时间（秒）
    
    # Worker 配置
    'worker_prefetch_multiplier': 1,  # Worker预取任务数量
    'worker_max_tasks_per_child': 1000,  # 每个Worker子进程最大任务数
    'worker_disable_rate_limits': False,  # 启用速率限制
    
    # 队列配置
    'task_default_queue': 'default',
    'task_default_exchange': 'default',
    'task_default_exchange_type': 'direct',
    'task_default_routing_key': 'default',
    
    # 任务路由
    'task_routes': {
        'app.celery_tasks.sync_orders': {'queue': 'sync_queue'},
        'app.celery_tasks.sync_full_orders': {'queue': 'sync_queue'},
        'app.celery_tasks.data_analysis': {'queue': 'analysis_queue'},
        'app.celery_tasks.custom_task': {'queue': 'default'},
    },
    
    # 定时任务配置
    'beat_schedule': {
        # 每小时同步订单
        'sync-orders-hourly': {
            'task': 'app.celery_tasks.sync_orders',
            'schedule': crontab(minute=0),
            'args': (24,),  # 同步最近24小时数据
            'options': {'queue': 'sync_queue'}
        },
        
        # 每天全量同步订单
        'sync-full-orders-daily': {
            'task': 'app.celery_tasks.sync_full_orders',
            'schedule': crontab(hour=2, minute=0),
            'args': (7,),  # 同步最近7天数据
            'options': {'queue': 'sync_queue'}
        },
        
        # 每天数据分析
        'data-analysis-daily': {
            'task': 'app.celery_tasks.data_analysis',
            'schedule': crontab(hour=3, minute=0),
            'options': {'queue': 'analysis_queue'}
        },
        
        # 每周数据清理
        'cleanup-weekly': {
            'task': 'app.celery_tasks.custom_task',
            'schedule': crontab(hour=1, minute=0, day_of_week=1),  # 每周一凌晨1点
            'args': ('cleanup_logs', {'days': 30}),
            'options': {'queue': 'default'}
        },
    },
    
    # 监控配置
    'worker_send_task_events': True,  # 发送任务事件
    'task_send_sent_event': True,  # 发送任务发送事件
}

# Flower 配置
FLOWER_CONFIG = {
    'port': 5555,
    'address': '0.0.0.0',
    'url_prefix': '',
    'basic_auth': None,  # 可以设置基础认证: ['user:password']
    'auto_refresh': True,
    'max_tasks': 10000,
}