# -*- coding: utf-8 -*-
"""
任务服务层
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from ..models import Task, TaskCreate, TaskStatus, TaskType
from ..utils import setup_logging, generate_task_id, format_response
from ..config import config

logger = setup_logging("task_service", config.log_level)


class TaskService:
    """任务服务类"""
    
    def __init__(self):
        # 内存存储任务（生产环境应使用数据库）
        self.tasks: Dict[str, Task] = {}
    
    async def create_task(self, task_create: TaskCreate) -> Task:
        """创建任务"""
        try:
            task_id = generate_task_id()
            
            task = Task(
                id=task_id,
                task_type=task_create.task_type,
                task_name=task_create.task_name,
                status=TaskStatus.PENDING,
                payload=task_create.payload,
                scheduled_at=task_create.scheduled_at,
                retry_count=task_create.retry_count,
                max_retries=task_create.max_retries,
                priority=task_create.priority,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.tasks[task_id] = task
            logger.info(f"创建任务: {task_id} - {task_create.task_name}")
            
            return task
            
        except Exception as e:
            logger.error(f"创建任务失败: {str(e)}")
            raise
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    async def get_tasks(self, 
                       status: Optional[TaskStatus] = None,
                       task_type: Optional[TaskType] = None,
                       limit: int = 100) -> List[Task]:
        """获取任务列表"""
        tasks = list(self.tasks.values())
        
        # 状态筛选
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        # 类型筛选
        if task_type:
            tasks = [t for t in tasks if t.task_type == task_type]
        
        # 按创建时间倒序排序
        tasks.sort(key=lambda x: x.created_at, reverse=True)
        
        return tasks[:limit]
    
    async def update_task_status(self, 
                               task_id: str, 
                               status: TaskStatus,
                               result: Optional[Dict[str, Any]] = None,
                               error_message: Optional[str] = None) -> Optional[Task]:
        """更新任务状态"""
        try:
            task = self.tasks.get(task_id)
            if not task:
                return None
            
            task.status = status
            task.updated_at = datetime.now()
            
            if status == TaskStatus.RUNNING:
                task.started_at = datetime.now()
            elif status in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                task.completed_at = datetime.now()
            
            if result:
                task.result = result
            
            if error_message:
                task.error_message = error_message
            
            logger.info(f"更新任务状态: {task_id} -> {status}")
            return task
            
        except Exception as e:
            logger.error(f"更新任务状态失败 {task_id}: {str(e)}")
            raise
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        try:
            task = self.tasks.get(task_id)
            if not task:
                return False
            
            if task.status in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                return False  # 已完成的任务无法取消
            
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            task.updated_at = datetime.now()
            
            logger.info(f"取消任务: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"取消任务失败 {task_id}: {str(e)}")
            return False
    
    async def retry_task(self, task_id: str) -> bool:
        """重试任务"""
        try:
            task = self.tasks.get(task_id)
            if not task:
                return False
            
            if task.retry_count >= task.max_retries:
                logger.warning(f"任务重试次数已达上限: {task_id}")
                return False
            
            task.retry_count += 1
            task.status = TaskStatus.RETRY
            task.started_at = None
            task.completed_at = None
            task.error_message = None
            task.updated_at = datetime.now()
            
            logger.info(f"重试任务: {task_id} (第{task.retry_count}次)")
            return True
            
        except Exception as e:
            logger.error(f"重试任务失败 {task_id}: {str(e)}")
            return False
    
    async def execute_task(self, task_id: str) -> bool:
        """执行任务"""
        try:
            task = self.tasks.get(task_id)
            if not task:
                return False
            
            # 更新为运行状态
            await self.update_task_status(task_id, TaskStatus.RUNNING)
            
            # 根据任务类型执行不同的逻辑
            success = await self._execute_task_by_type(task)
            
            if success:
                await self.update_task_status(
                    task_id, 
                    TaskStatus.SUCCESS,
                    result={"message": "任务执行成功", "timestamp": datetime.now().isoformat()}
                )
            else:
                await self.update_task_status(
                    task_id, 
                    TaskStatus.FAILED,
                    error_message="任务执行失败"
                )
            
            return success
            
        except Exception as e:
            logger.error(f"执行任务失败 {task_id}: {str(e)}")
            await self.update_task_status(task_id, TaskStatus.FAILED, error_message=str(e))
            return False
    
    async def _execute_task_by_type(self, task: Task) -> bool:
        """根据任务类型执行任务"""
        try:
            if task.task_type == TaskType.ORDER_TIMEOUT:
                return await self._handle_order_timeout(task)
            elif task.task_type == TaskType.PAYMENT_TIMEOUT:
                return await self._handle_payment_timeout(task)
            elif task.task_type == TaskType.QR_CODE_GENERATION:
                return await self._handle_qr_code_generation(task)
            elif task.task_type == TaskType.NOTIFICATION:
                return await self._handle_notification(task)
            elif task.task_type == TaskType.DATA_SYNC:
                return await self._handle_data_sync(task)
            elif task.task_type == TaskType.CLEANUP:
                return await self._handle_cleanup(task)
            else:
                logger.warning(f"未知任务类型: {task.task_type}")
                return False
                
        except Exception as e:
            logger.error(f"执行任务类型处理失败 {task.id}: {str(e)}")
            return False
    
    async def _handle_order_timeout(self, task: Task) -> bool:
        """处理订单超时"""
        logger.info(f"处理订单超时任务: {task.id}")
        # 模拟处理逻辑
        await asyncio.sleep(1)
        return True
    
    async def _handle_payment_timeout(self, task: Task) -> bool:
        """处理支付超时"""
        logger.info(f"处理支付超时任务: {task.id}")
        # 模拟处理逻辑
        await asyncio.sleep(1)
        return True
    
    async def _handle_qr_code_generation(self, task: Task) -> bool:
        """处理二维码生成"""
        logger.info(f"处理二维码生成任务: {task.id}")
        # 模拟处理逻辑
        await asyncio.sleep(2)
        return True
    
    async def _handle_notification(self, task: Task) -> bool:
        """处理通知发送"""
        logger.info(f"处理通知发送任务: {task.id}")
        # 模拟处理逻辑
        await asyncio.sleep(0.5)
        return True
    
    async def _handle_data_sync(self, task: Task) -> bool:
        """处理数据同步"""
        logger.info(f"处理数据同步任务: {task.id}")
        # 模拟处理逻辑
        await asyncio.sleep(3)
        return True
    
    async def _handle_cleanup(self, task: Task) -> bool:
        """处理清理任务"""
        logger.info(f"处理清理任务: {task.id}")
        # 模拟处理逻辑
        await asyncio.sleep(1)
        return True
    
    async def cleanup_expired_tasks(self, days: int = 7) -> int:
        """清理过期任务"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            expired_tasks = []
            
            for task_id, task in self.tasks.items():
                if (task.status in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                    task.completed_at and task.completed_at < cutoff_time):
                    expired_tasks.append(task_id)
            
            for task_id in expired_tasks:
                del self.tasks[task_id]
            
            logger.info(f"清理过期任务完成，删除 {len(expired_tasks)} 个任务")
            return len(expired_tasks)
            
        except Exception as e:
            logger.error(f"清理过期任务失败: {str(e)}")
            return 0
    
    async def get_task_statistics(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        try:
            total = len(self.tasks)
            status_counts = {}
            type_counts = {}
            
            for task in self.tasks.values():
                # 状态统计
                status_counts[task.status] = status_counts.get(task.status, 0) + 1
                # 类型统计
                type_counts[task.task_type] = type_counts.get(task.task_type, 0) + 1
            
            return {
                "total_tasks": total,
                "status_distribution": status_counts,
                "type_distribution": type_counts,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取任务统计失败: {str(e)}")
            return {}