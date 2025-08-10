#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 调度服务业务逻辑

处理定时任务、延迟发送、重试机制等调度相关功能
"""

import uuid
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_

from ..models.notification import Notification, NotificationStatus, NotificationPriority
from ..models.channel import NotificationChannel, ChannelStatus
from ..core.config import get_config
from ..core.database import get_db

import logging

logger = logging.getLogger(__name__)
config = get_config()


class TaskType(Enum):
    """任务类型"""
    SEND_NOTIFICATION = "send_notification"
    RETRY_NOTIFICATION = "retry_notification"
    CLEANUP_EXPIRED = "cleanup_expired"
    CHANNEL_HEALTH_CHECK = "channel_health_check"
    BATCH_SEND = "batch_send"
    SCHEDULED_SEND = "scheduled_send"


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    """调度任务"""
    id: str
    type: TaskType
    status: TaskStatus
    scheduled_at: datetime
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    retry_delay: int = 60  # 秒
    payload: Dict[str, Any] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.payload is None:
            self.payload = {}


class SchedulerService:
    """
    调度服务业务逻辑类
    
    处理定时任务、延迟发送、重试机制等调度相关功能
    """
    
    def __init__(self):
        # 任务队列 {task_id: ScheduledTask}
        self.tasks: Dict[str, ScheduledTask] = {}
        
        # 任务处理器映射
        self.task_handlers: Dict[TaskType, Callable] = {
            TaskType.SEND_NOTIFICATION: self._handle_send_notification,
            TaskType.RETRY_NOTIFICATION: self._handle_retry_notification,
            TaskType.CLEANUP_EXPIRED: self._handle_cleanup_expired,
            TaskType.CHANNEL_HEALTH_CHECK: self._handle_channel_health_check,
            TaskType.BATCH_SEND: self._handle_batch_send,
            TaskType.SCHEDULED_SEND: self._handle_scheduled_send,
        }
        
        # 运行状态
        self._running = False
        self._worker_tasks: List[asyncio.Task] = []
        
        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "retry_tasks": 0,
            "cancelled_tasks": 0
        }
    
    async def start(self, worker_count: int = 3):
        """
        启动调度服务
        
        Args:
            worker_count: 工作线程数量
        """
        if self._running:
            logger.warning("Scheduler service is already running")
            return
        
        self._running = True
        
        # 启动工作线程
        for i in range(worker_count):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            self._worker_tasks.append(task)
        
        # 启动清理任务
        cleanup_task = asyncio.create_task(self._cleanup_worker())
        self._worker_tasks.append(cleanup_task)
        
        # 启动健康检查任务
        health_check_task = asyncio.create_task(self._health_check_worker())
        self._worker_tasks.append(health_check_task)
        
        logger.info(f"Scheduler service started with {worker_count} workers")
    
    async def stop(self):
        """
        停止调度服务
        """
        if not self._running:
            return
        
        self._running = False
        
        # 取消所有工作任务
        for task in self._worker_tasks:
            task.cancel()
        
        # 等待任务完成
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()
        
        logger.info("Scheduler service stopped")
    
    async def schedule_task(
        self,
        task_type: TaskType,
        payload: Dict[str, Any],
        scheduled_at: Optional[datetime] = None,
        max_retries: int = 3,
        retry_delay: int = 60
    ) -> str:
        """
        调度任务
        
        Args:
            task_type: 任务类型
            payload: 任务载荷
            scheduled_at: 调度时间（默认立即执行）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            
        Returns:
            str: 任务ID
        """
        if scheduled_at is None:
            scheduled_at = datetime.utcnow()
        
        task_id = str(uuid.uuid4())
        task = ScheduledTask(
            id=task_id,
            type=task_type,
            status=TaskStatus.PENDING,
            scheduled_at=scheduled_at,
            created_at=datetime.utcnow(),
            max_retries=max_retries,
            retry_delay=retry_delay,
            payload=payload
        )
        
        self.tasks[task_id] = task
        self.stats["total_tasks"] += 1
        
        logger.info(f"Scheduled task {task_id} of type {task_type.value} for {scheduled_at}")
        return task_id
    
    async def schedule_notification(
        self,
        notification_id: uuid.UUID,
        channel_id: uuid.UUID,
        scheduled_at: Optional[datetime] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL
    ) -> str:
        """
        调度通知发送
        
        Args:
            notification_id: 通知ID
            channel_id: 渠道ID
            scheduled_at: 调度时间
            priority: 优先级
            
        Returns:
            str: 任务ID
        """
        payload = {
            "notification_id": str(notification_id),
            "channel_id": str(channel_id),
            "priority": priority.value
        }
        
        return await self.schedule_task(
            TaskType.SEND_NOTIFICATION,
            payload,
            scheduled_at
        )
    
    async def schedule_retry(
        self,
        notification_id: uuid.UUID,
        channel_id: uuid.UUID,
        retry_count: int,
        delay_minutes: int = 5
    ) -> str:
        """
        调度重试发送
        
        Args:
            notification_id: 通知ID
            channel_id: 渠道ID
            retry_count: 重试次数
            delay_minutes: 延迟分钟数
            
        Returns:
            str: 任务ID
        """
        scheduled_at = datetime.utcnow() + timedelta(minutes=delay_minutes)
        
        payload = {
            "notification_id": str(notification_id),
            "channel_id": str(channel_id),
            "retry_count": retry_count
        }
        
        return await self.schedule_task(
            TaskType.RETRY_NOTIFICATION,
            payload,
            scheduled_at,
            max_retries=1  # 重试任务本身不再重试
        )
    
    async def schedule_batch_send(
        self,
        notification_ids: List[uuid.UUID],
        channel_id: uuid.UUID,
        scheduled_at: Optional[datetime] = None,
        batch_size: int = 10
    ) -> str:
        """
        调度批量发送
        
        Args:
            notification_ids: 通知ID列表
            channel_id: 渠道ID
            scheduled_at: 调度时间
            batch_size: 批次大小
            
        Returns:
            str: 任务ID
        """
        payload = {
            "notification_ids": [str(nid) for nid in notification_ids],
            "channel_id": str(channel_id),
            "batch_size": batch_size
        }
        
        return await self.schedule_task(
            TaskType.BATCH_SEND,
            payload,
            scheduled_at
        )
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否取消成功
        """
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return False
        
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.utcnow()
        self.stats["cancelled_tasks"] += 1
        
        logger.info(f"Cancelled task {task_id}")
        return True
    
    async def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """
        获取任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[ScheduledTask]: 任务对象
        """
        return self.tasks.get(task_id)
    
    async def get_tasks(
        self,
        task_type: Optional[TaskType] = None,
        status: Optional[TaskStatus] = None,
        limit: int = 100
    ) -> List[ScheduledTask]:
        """
        获取任务列表
        
        Args:
            task_type: 任务类型过滤
            status: 状态过滤
            limit: 限制数量
            
        Returns:
            List[ScheduledTask]: 任务列表
        """
        tasks = list(self.tasks.values())
        
        # 过滤
        if task_type:
            tasks = [t for t in tasks if t.type == task_type]
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        # 排序（最新的在前）
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        return tasks[:limit]
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        pending_count = len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING])
        running_count = len([t for t in self.tasks.values() if t.status == TaskStatus.RUNNING])
        
        return {
            **self.stats,
            "pending_tasks": pending_count,
            "running_tasks": running_count,
            "total_in_memory": len(self.tasks),
            "is_running": self._running,
            "worker_count": len(self._worker_tasks)
        }
    
    async def _worker(self, worker_name: str):
        """
        工作线程
        
        Args:
            worker_name: 工作线程名称
        """
        logger.info(f"Scheduler worker {worker_name} started")
        
        while self._running:
            try:
                # 查找待执行的任务
                task = await self._get_next_task()
                
                if task:
                    await self._execute_task(task, worker_name)
                else:
                    # 没有任务，等待一段时间
                    await asyncio.sleep(1)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler worker {worker_name}: {str(e)}")
                await asyncio.sleep(5)
        
        logger.info(f"Scheduler worker {worker_name} stopped")
    
    async def _get_next_task(self) -> Optional[ScheduledTask]:
        """
        获取下一个待执行的任务
        
        Returns:
            Optional[ScheduledTask]: 任务对象
        """
        now = datetime.utcnow()
        
        # 查找待执行的任务
        pending_tasks = [
            task for task in self.tasks.values()
            if task.status == TaskStatus.PENDING and task.scheduled_at <= now
        ]
        
        if not pending_tasks:
            return None
        
        # 按优先级和调度时间排序
        def task_priority(task):
            priority_weight = {
                "high": 3,
                "normal": 2,
                "low": 1
            }
            
            payload_priority = task.payload.get("priority", "normal")
            weight = priority_weight.get(payload_priority, 2)
            
            # 优先级高的先执行，同优先级按调度时间排序
            return (-weight, task.scheduled_at)
        
        pending_tasks.sort(key=task_priority)
        return pending_tasks[0]
    
    async def _execute_task(self, task: ScheduledTask, worker_name: str):
        """
        执行任务
        
        Args:
            task: 任务对象
            worker_name: 工作线程名称
        """
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        
        logger.info(f"Worker {worker_name} executing task {task.id} of type {task.type.value}")
        
        try:
            # 获取任务处理器
            handler = self.task_handlers.get(task.type)
            if not handler:
                raise Exception(f"No handler for task type {task.type.value}")
            
            # 执行任务
            result = await handler(task.payload)
            
            # 任务成功
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.result = result
            self.stats["completed_tasks"] += 1
            
            logger.info(f"Task {task.id} completed successfully")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Task {task.id} failed: {error_msg}")
            
            # 检查是否需要重试
            if task.retry_count < task.max_retries:
                # 安排重试
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                task.scheduled_at = datetime.utcnow() + timedelta(seconds=task.retry_delay)
                task.error = error_msg
                self.stats["retry_tasks"] += 1
                
                logger.info(f"Task {task.id} scheduled for retry {task.retry_count}/{task.max_retries}")
            else:
                # 重试次数用完，标记为失败
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.utcnow()
                task.error = error_msg
                self.stats["failed_tasks"] += 1
                
                logger.error(f"Task {task.id} failed permanently after {task.retry_count} retries")
    
    async def _handle_send_notification(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理发送通知任务
        
        Args:
            payload: 任务载荷
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        notification_id = uuid.UUID(payload["notification_id"])
        channel_id = uuid.UUID(payload["channel_id"])
        
        # 这里应该调用实际的发送服务
        # 为了演示，这里只是模拟
        await asyncio.sleep(0.1)
        
        return {
            "notification_id": str(notification_id),
            "channel_id": str(channel_id),
            "status": "sent",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_retry_notification(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理重试通知任务
        
        Args:
            payload: 任务载荷
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        notification_id = uuid.UUID(payload["notification_id"])
        channel_id = uuid.UUID(payload["channel_id"])
        retry_count = payload["retry_count"]
        
        # 这里应该调用实际的发送服务
        await asyncio.sleep(0.1)
        
        return {
            "notification_id": str(notification_id),
            "channel_id": str(channel_id),
            "retry_count": retry_count,
            "status": "retried",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_cleanup_expired(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理清理过期通知任务
        
        Args:
            payload: 任务载荷
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        # 这里应该实现实际的清理逻辑
        await asyncio.sleep(0.1)
        
        return {
            "cleaned_count": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_channel_health_check(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理渠道健康检查任务
        
        Args:
            payload: 任务载荷
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        # 这里应该实现实际的健康检查逻辑
        await asyncio.sleep(0.1)
        
        return {
            "checked_channels": 0,
            "healthy_channels": 0,
            "unhealthy_channels": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_batch_send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理批量发送任务
        
        Args:
            payload: 任务载荷
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        notification_ids = [uuid.UUID(nid) for nid in payload["notification_ids"]]
        channel_id = uuid.UUID(payload["channel_id"])
        batch_size = payload.get("batch_size", 10)
        
        # 这里应该实现实际的批量发送逻辑
        await asyncio.sleep(0.1)
        
        return {
            "notification_count": len(notification_ids),
            "channel_id": str(channel_id),
            "batch_size": batch_size,
            "status": "sent",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_scheduled_send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理定时发送任务
        
        Args:
            payload: 任务载荷
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        # 这里应该实现实际的定时发送逻辑
        await asyncio.sleep(0.1)
        
        return {
            "status": "sent",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _cleanup_worker(self):
        """
        清理工作线程
        
        定期清理已完成的任务和过期数据
        """
        logger.info("Cleanup worker started")
        
        while self._running:
            try:
                await asyncio.sleep(3600)  # 每小时执行一次
                
                # 清理已完成的任务（保留最近24小时的）
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                
                completed_tasks = [
                    task_id for task_id, task in self.tasks.items()
                    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                    and task.completed_at and task.completed_at < cutoff_time
                ]
                
                for task_id in completed_tasks:
                    del self.tasks[task_id]
                
                if completed_tasks:
                    logger.info(f"Cleaned up {len(completed_tasks)} old tasks")
                
                # 调度清理过期通知任务
                await self.schedule_task(
                    TaskType.CLEANUP_EXPIRED,
                    {"cutoff_hours": 72}
                )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup worker: {str(e)}")
        
        logger.info("Cleanup worker stopped")
    
    async def _health_check_worker(self):
        """
        健康检查工作线程
        
        定期检查渠道健康状态
        """
        logger.info("Health check worker started")
        
        while self._running:
            try:
                await asyncio.sleep(1800)  # 每30分钟执行一次
                
                # 调度渠道健康检查任务
                await self.schedule_task(
                    TaskType.CHANNEL_HEALTH_CHECK,
                    {}
                )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check worker: {str(e)}")
        
        logger.info("Health check worker stopped")


# 全局调度服务实例
scheduler_service = SchedulerService()