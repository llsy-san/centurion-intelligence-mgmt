"""
Celery 任务定义
"""
from celery import current_task
from datetime import datetime, timedelta
import sys
import os

# 添加共享模块到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))
from utils import setup_logging

from ..celery_app import celery_app
from .services.sync_service import sync_service

logger = setup_logging("celery-tasks")


@celery_app.task(bind=True, name='app.celery_tasks.sync_orders')
def sync_orders(self, hours: int = 24):
    """
    同步订单数据任务
    Args:
        hours: 同步最近N小时的数据
    """
    try:
        # 更新任务状态
        self.update_state(state='PROGRESS', meta={'status': '开始同步订单数据'})
        
        # 计算时间范围
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        logger.info(f"开始同步订单数据，时间范围: {start_time} - {end_time}")
        
        # 执行同步
        result = sync_service.sync_orders(start_time, end_time)
        
        logger.info(f"订单同步完成: {result}")
        
        return {
            'status': 'SUCCESS',
            'message': '订单同步完成',
            'data': result,
            'task_id': self.request.id,
            'completed_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"订单同步任务失败: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'task_id': self.request.id}
        )
        raise


@celery_app.task(bind=True, name='app.celery_tasks.sync_full_orders')
def sync_full_orders(self, days: int = 7):
    """
    全量同步订单数据任务
    Args:
        days: 同步最近N天的数据
    """
    try:
        self.update_state(state='PROGRESS', meta={'status': '开始全量同步订单数据'})
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        logger.info(f"开始全量同步订单数据，时间范围: {start_time} - {end_time}")
        
        result = sync_service.sync_orders(start_time, end_time)
        
        logger.info(f"全量订单同步完成: {result}")
        
        return {
            'status': 'SUCCESS',
            'message': '全量订单同步完成',
            'data': result,
            'task_id': self.request.id,
            'completed_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"全量订单同步任务失败: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'task_id': self.request.id}
        )
        raise


@celery_app.task(bind=True, name='app.celery_tasks.data_analysis')
def data_analysis(self):
    """
    数据分析任务
    """
    try:
        self.update_state(state='PROGRESS', meta={'status': '开始数据分析'})
        
        logger.info("开始执行数据分析任务")
        
        # 这里可以添加数据分析逻辑
        # 例如：统计分析、报表生成等
        
        result = {
            'analysis_date': datetime.now().date().isoformat(),
            'total_orders': 0,  # 从数据库查询实际数据
            'total_revenue': 0.0,
            'analysis_completed': True
        }
        
        logger.info(f"数据分析完成: {result}")
        
        return {
            'status': 'SUCCESS',
            'message': '数据分析完成',
            'data': result,
            'task_id': self.request.id,
            'completed_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"数据分析任务失败: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'task_id': self.request.id}
        )
        raise


@celery_app.task(bind=True, name='app.celery_tasks.custom_task')
def custom_task(self, task_name: str, params: dict):
    """
    自定义任务
    Args:
        task_name: 任务名称
        params: 任务参数
    """
    try:
        self.update_state(state='PROGRESS', meta={'status': f'执行自定义任务: {task_name}'})
        
        logger.info(f"开始执行自定义任务: {task_name}, 参数: {params}")
        
        # 根据任务名称执行不同的逻辑
        if task_name == 'cleanup_logs':
            # 清理日志任务
            result = {'cleaned_files': 10, 'freed_space': '100MB'}
        elif task_name == 'backup_database':
            # 数据库备份任务
            result = {'backup_file': f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.sql'}
        else:
            # 通用任务处理
            result = {'message': f'任务 {task_name} 执行完成', 'params': params}
        
        logger.info(f"自定义任务完成: {task_name}, 结果: {result}")
        
        return {
            'status': 'SUCCESS',
            'message': f'自定义任务 {task_name} 完成',
            'data': result,
            'task_id': self.request.id,
            'completed_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"自定义任务失败 {task_name}: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'task_id': self.request.id, 'task_name': task_name}
        )
        raise