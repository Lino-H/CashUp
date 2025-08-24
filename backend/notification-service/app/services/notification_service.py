#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 通知服务核心业务逻辑

处理通知的创建、发送、状态管理等核心业务逻辑
"""

import uuid
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import selectinload

from ..models.notification import Notification, NotificationStatus, NotificationPriority, NotificationCategory
from ..models.template import NotificationTemplate
from ..models.channel import NotificationChannel, ChannelStatus
from ..schemas.notification import (
    NotificationCreate, NotificationUpdate, NotificationFilter,
    NotificationBatchCreate, NotificationStatusUpdate
)
from ..core.exceptions import (
    NotificationNotFoundError, TemplateNotFoundError, ChannelNotFoundError,
    InvalidNotificationError, NotificationExpiredError
)
from ..core.config import get_config
from .template_service import TemplateService
from .channel_service import ChannelService
from .sender_service import SenderService
from .websocket_service import WebSocketService

import logging

logger = logging.getLogger(__name__)
config = get_config()


class NotificationService:
    """
    通知服务核心业务逻辑类
    
    负责处理通知的创建、发送、状态管理等核心业务逻辑
    """
    
    def __init__(
        self,
        template_service: TemplateService,
        channel_service: ChannelService,
        sender_service: SenderService,
        websocket_service: WebSocketService
    ):
        self.template_service = template_service
        self.channel_service = channel_service
        self.sender_service = sender_service
        self.websocket_service = websocket_service
    
    async def create_notification(
        self,
        db: AsyncSession,
        notification_data: NotificationCreate,
        user_id: Optional[uuid.UUID] = None
    ) -> Notification:
        """
        创建通知
        
        Args:
            db: 数据库会话
            notification_data: 通知创建数据
            user_id: 用户ID
            
        Returns:
            Notification: 创建的通知
            
        Raises:
            TemplateNotFoundError: 模板不存在
            ChannelNotFoundError: 渠道不存在
            InvalidNotificationError: 无效的通知数据
        """
        notification_id = str(uuid.uuid4())[:8]
        logger.info(f"[Service-{notification_id}] 开始创建通知 - 标题: {notification_data.title}, 渠道: {notification_data.channels}")
        
        try:
            # 验证模板（如果指定）
            template = None
            if notification_data.template_id:
                logger.info(f"[Service-{notification_id}] 验证模板: {notification_data.template_id}")
                template = await self.template_service.get_template(
                    db, notification_data.template_id
                )
                if not template:
                    logger.error(f"[Service-{notification_id}] 模板不存在: {notification_data.template_id}")
                    raise TemplateNotFoundError(f"Template {notification_data.template_id} not found")
                logger.info(f"[Service-{notification_id}] 模板验证成功")
            
            # 验证渠道
            logger.info(f"[Service-{notification_id}] 开始验证渠道: {notification_data.channels}")
            for channel_name in notification_data.channels:
                logger.info(f"[Service-{notification_id}] 验证渠道: {channel_name}")
                channel = await self.channel_service.get_channel_by_name(db, channel_name)
                if not channel:
                    logger.error(f"[Service-{notification_id}] 渠道不存在: {channel_name}")
                    raise ChannelNotFoundError(f"Channel {channel_name} not found")
                if not channel.is_active:
                    logger.error(f"[Service-{notification_id}] 渠道未激活: {channel_name}")
                    raise InvalidNotificationError(f"Channel {channel_name} is not active")
                logger.info(f"[Service-{notification_id}] 渠道验证成功: {channel_name}")
            logger.info(f"[Service-{notification_id}] 所有渠道验证完成")
            
            # 处理收件人信息
            recipient_email = None
            recipient_phone = None
            recipient_data = notification_data.recipients
            
            # 从recipients中提取邮箱和手机号
            if notification_data.recipients:
                if 'email' in notification_data.recipients and notification_data.recipients['email']:
                    recipient_email = notification_data.recipients['email'][0]
                if 'sms' in notification_data.recipients and notification_data.recipients['sms']:
                    recipient_phone = notification_data.recipients['sms'][0]
            
            # 创建通知对象
            notification = Notification(
                id=uuid.uuid4(),
                user_id=user_id or notification_data.user_id,
                title=notification_data.title,
                content=notification_data.content,
                category=notification_data.category,
                priority=notification_data.priority,
                status=NotificationStatus.PENDING,
                channels=','.join(notification_data.channels) if notification_data.channels else None,
                template_id=notification_data.template_id,
                template_data=notification_data.template_variables or {},
                recipient_email=recipient_email,
                recipient_phone=recipient_phone,
                recipient_data=recipient_data,
                send_immediately=notification_data.scheduled_at is None,
                scheduled_at=notification_data.scheduled_at,
                expires_at=notification_data.expires_at,
                max_retry_attempts=config.NOTIFICATION_MAX_RETRY_ATTEMPTS,
                retry_attempts=0,
                retry_delay_seconds=60,
                meta_data=notification_data.metadata or {},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # 保存到数据库
            logger.info(f"[Service-{notification_id}] 开始保存通知到数据库")
            db.add(notification)
            await db.commit()
            await db.refresh(notification)
            logger.info(f"[Service-{notification_id}] 通知保存成功 - 数据库ID: {notification.id}")
            
            logger.info(f"Created notification {notification.id} for user {user_id}")
            
            # 如果不是定时发送，立即处理
            if not notification.scheduled_at:
                logger.info(f"[Service-{notification_id}] 开始立即处理通知发送")
                await self._process_notification(db, notification)
                logger.info(f"[Service-{notification_id}] 通知处理完成")
            else:
                logger.info(f"[Service-{notification_id}] 通知已安排定时发送: {notification.scheduled_at}")
            
            return notification
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create notification: {str(e)}")
            raise
    
    async def create_batch_notifications(
        self,
        db: AsyncSession,
        batch_data: NotificationBatchCreate,
        user_id: Optional[uuid.UUID] = None
    ) -> Tuple[List[Notification], List[Dict[str, Any]]]:
        """
        批量创建通知
        
        Args:
            db: 数据库会话
            batch_data: 批量创建数据
            user_id: 用户ID
            
        Returns:
            Tuple[List[Notification], List[Dict[str, Any]]]: 成功创建的通知列表和失败项目列表
        """
        notifications = []
        failed_items = []
        
        for i, notification_data in enumerate(batch_data.notifications):
            try:
                notification = await self.create_notification(db, notification_data, user_id)
                notifications.append(notification)
            except Exception as e:
                failed_items.append({
                    "index": i,
                    "data": notification_data.model_dump(),
                    "error": str(e)
                })
                logger.error(f"Failed to create notification at index {i}: {str(e)}")
        
        logger.info(f"Batch created {len(notifications)} notifications, {len(failed_items)} failed")
        return notifications, failed_items
    
    async def get_notification(
        self,
        db: AsyncSession,
        notification_id: uuid.UUID
    ) -> Optional[Notification]:
        """
        获取通知详情
        
        Args:
            db: 数据库会话
            notification_id: 通知ID
            
        Returns:
            Optional[Notification]: 通知对象
        """
        result = await db.execute(
            select(Notification)
            .where(Notification.id == notification_id)
            .options(selectinload(Notification.template))
        )
        return result.scalar_one_or_none()
    
    async def get_notifications(
        self,
        db: AsyncSession,
        filters: NotificationFilter,
        page: int = 1,
        size: int = 20
    ) -> Tuple[List[Notification], int]:
        """
        获取通知列表
        
        Args:
            db: 数据库会话
            filters: 过滤条件
            page: 页码
            size: 每页大小
            
        Returns:
            Tuple[List[Notification], int]: 通知列表和总数
        """
        # 构建查询条件
        conditions = []
        
        if filters.user_id:
            conditions.append(Notification.user_id == filters.user_id)
        
        if filters.category:
            conditions.append(Notification.category == filters.category)
        
        if filters.priority:
            conditions.append(Notification.priority == filters.priority)
        
        if filters.status:
            conditions.append(Notification.status == filters.status)
        
        if filters.channel:
            conditions.append(Notification.channels.contains([filters.channel]))
        
        if filters.template_id:
            conditions.append(Notification.template_id == filters.template_id)
        
        if filters.is_scheduled is not None:
            if filters.is_scheduled:
                conditions.append(Notification.scheduled_at.isnot(None))
            else:
                conditions.append(Notification.scheduled_at.is_(None))
        
        if filters.is_expired is not None:
            now = datetime.utcnow()
            if filters.is_expired:
                conditions.append(
                    and_(
                        Notification.expires_at.isnot(None),
                        Notification.expires_at < now
                    )
                )
            else:
                conditions.append(
                    or_(
                        Notification.expires_at.is_(None),
                        Notification.expires_at >= now
                    )
                )
        
        if filters.has_error is not None:
            if filters.has_error:
                conditions.append(Notification.error_message.isnot(None))
            else:
                conditions.append(Notification.error_message.is_(None))
        
        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(
                or_(
                    Notification.title.ilike(search_term),
                    Notification.content.ilike(search_term)
                )
            )
        
        if filters.start_date:
            conditions.append(Notification.created_at >= filters.start_date)
        
        if filters.end_date:
            conditions.append(Notification.created_at <= filters.end_date)
        
        # 查询总数
        count_query = select(func.count(Notification.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # 查询数据
        query = select(Notification).options(selectinload(Notification.template))
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(Notification.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)
        
        result = await db.execute(query)
        notifications = result.scalars().all()
        
        return list(notifications), total
    
    async def update_notification(
        self,
        db: AsyncSession,
        notification_id: uuid.UUID,
        update_data: NotificationUpdate
    ) -> Optional[Notification]:
        """
        更新通知
        
        Args:
            db: 数据库会话
            notification_id: 通知ID
            update_data: 更新数据
            
        Returns:
            Optional[Notification]: 更新后的通知
            
        Raises:
            NotificationNotFoundError: 通知不存在
            InvalidNotificationError: 无效的更新数据
        """
        notification = await self.get_notification(db, notification_id)
        if not notification:
            raise NotificationNotFoundError(f"Notification {notification_id} not found")
        
        # 检查是否可以更新
        if notification.status in [NotificationStatus.SENT, NotificationStatus.DELIVERED, NotificationStatus.READ]:
            raise InvalidNotificationError("Cannot update sent notification")
        
        # 更新字段
        update_fields = update_data.model_dump(exclude_none=True)
        for field, value in update_fields.items():
            setattr(notification, field, value)
        
        notification.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(notification)
        
        logger.info(f"Updated notification {notification_id}")
        return notification
    
    async def update_notification_status(
        self,
        db: AsyncSession,
        notification_id: uuid.UUID,
        status_update: NotificationStatusUpdate
    ) -> Optional[Notification]:
        """
        更新通知状态
        
        Args:
            db: 数据库会话
            notification_id: 通知ID
            status_update: 状态更新数据
            
        Returns:
            Optional[Notification]: 更新后的通知
        """
        notification = await self.get_notification(db, notification_id)
        if not notification:
            raise NotificationNotFoundError(f"Notification {notification_id} not found")
        
        # 更新状态
        notification.status = status_update.status
        
        if status_update.error_message:
            notification.error_message = status_update.error_message
        
        if status_update.retry_attempts is not None:
                notification.retry_attempts = status_update.retry_attempts
        
        # 设置发送时间
        if status_update.status == NotificationStatus.SENT and not notification.sent_at:
            notification.sent_at = datetime.utcnow()
        
        notification.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(notification)
        
        # 发送WebSocket通知
        if notification.user_id:
            await self.websocket_service.send_notification_update(
                notification,
                update_type="status_update",
                target_type="user",
                target_value=str(notification.user_id)
            )
        
        logger.info(f"Updated notification {notification_id} status to {status_update.status}")
        return notification
    
    async def delete_notification(
        self,
        db: AsyncSession,
        notification_id: uuid.UUID
    ) -> bool:
        """
        删除通知
        
        Args:
            db: 数据库会话
            notification_id: 通知ID
            
        Returns:
            bool: 是否删除成功
        """
        result = await db.execute(
            delete(Notification).where(Notification.id == notification_id)
        )
        await db.commit()
        
        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"Deleted notification {notification_id}")
        
        return deleted
    
    async def retry_notification(
        self,
        db: AsyncSession,
        notification_id: uuid.UUID,
        force: bool = False
    ) -> bool:
        """
        重试发送通知
        
        Args:
            db: 数据库会话
            notification_id: 通知ID
            force: 是否强制重试
            
        Returns:
            bool: 是否重试成功
            
        Raises:
            NotificationNotFoundError: 通知不存在
            InvalidNotificationError: 无效的重试请求
        """
        notification = await self.get_notification(db, notification_id)
        if not notification:
            raise NotificationNotFoundError(f"Notification {notification_id} not found")
        
        # 检查是否可以重试
        if not force:
            if notification.status != NotificationStatus.FAILED:
                raise InvalidNotificationError("Only failed notifications can be retried")
            
            if notification.retry_attempts >= notification.max_retry_attempts:
                raise InvalidNotificationError("Maximum retry attempts exceeded")
            
            # 检查是否过期
            if notification.expires_at and notification.expires_at < datetime.utcnow():
                raise NotificationExpiredError("Notification has expired")
        
        # 重置状态
        notification.status = NotificationStatus.PENDING
        notification.error_message = None
        notification.updated_at = datetime.utcnow()
        
        await db.commit()
        
        # 重新处理通知
        await self._process_notification(db, notification)
        
        logger.info(f"Retrying notification {notification_id}")
        return True
    
    async def cancel_notification(
        self,
        db: AsyncSession,
        notification_id: uuid.UUID,
        reason: Optional[str] = None
    ) -> bool:
        """
        取消通知
        
        Args:
            db: 数据库会话
            notification_id: 通知ID
            reason: 取消原因
            
        Returns:
            bool: 是否取消成功
        """
        notification = await self.get_notification(db, notification_id)
        if not notification:
            raise NotificationNotFoundError(f"Notification {notification_id} not found")
        
        # 检查是否可以取消
        if notification.status in [NotificationStatus.SENT, NotificationStatus.DELIVERED, NotificationStatus.READ]:
            raise InvalidNotificationError("Cannot cancel sent notification")
        
        # 更新状态
        notification.status = NotificationStatus.CANCELLED
        if reason:
            notification.error_message = f"Cancelled: {reason}"
        notification.updated_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"Cancelled notification {notification_id}: {reason}")
        return True
    
    async def get_notification_stats(
        self,
        db: AsyncSession,
        user_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取通知统计信息
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        conditions = []
        
        if user_id:
            conditions.append(Notification.user_id == user_id)
        
        if start_date:
            conditions.append(Notification.created_at >= start_date)
        
        if end_date:
            conditions.append(Notification.created_at <= end_date)
        
        base_query = select(Notification)
        if conditions:
            base_query = base_query.where(and_(*conditions))
        
        # 总数统计
        total_query = select(func.count(Notification.id))
        if conditions:
            total_query = total_query.where(and_(*conditions))
        
        total_result = await db.execute(total_query)
        total = total_result.scalar()
        
        # 按状态统计
        status_query = select(
            Notification.status,
            func.count(Notification.id)
        ).group_by(Notification.status)
        if conditions:
            status_query = status_query.where(and_(*conditions))
        
        status_result = await db.execute(status_query)
        status_stats = {status.value: count for status, count in status_result.fetchall()}
        
        # 按分类统计
        category_query = select(
            Notification.category,
            func.count(Notification.id)
        ).group_by(Notification.category)
        if conditions:
            category_query = category_query.where(and_(*conditions))
        
        category_result = await db.execute(category_query)
        category_stats = {category.value if category else 'unknown': count for category, count in category_result.fetchall()}
        
        # 按优先级统计
        priority_query = select(
            Notification.priority,
            func.count(Notification.id)
        ).group_by(Notification.priority)
        if conditions:
            priority_query = priority_query.where(and_(*conditions))
        
        priority_result = await db.execute(priority_query)
        priority_stats = {priority.value if priority else 'unknown': count for priority, count in priority_result.fetchall()}
        
        # 计算成功率
        success_count = (
            status_stats.get(NotificationStatus.SENT.value, 0) +
            status_stats.get(NotificationStatus.DELIVERED.value, 0) +
            status_stats.get(NotificationStatus.READ.value, 0)
        )
        success_rate = success_count / total if total > 0 else 0.0
        
        return {
            "total": total,
            "pending": status_stats.get(NotificationStatus.PENDING.value, 0),
            "sent": status_stats.get(NotificationStatus.SENT.value, 0),
            "delivered": status_stats.get(NotificationStatus.DELIVERED.value, 0),
            "read": status_stats.get(NotificationStatus.READ.value, 0),
            "failed": status_stats.get(NotificationStatus.FAILED.value, 0),
            "expired": status_stats.get(NotificationStatus.EXPIRED.value, 0),
            "by_category": category_stats,
            "by_priority": priority_stats,
            "success_rate": success_rate
        }
    
    async def process_scheduled_notifications(self, db: AsyncSession) -> int:
        """
        处理定时通知
        
        Args:
            db: 数据库会话
            
        Returns:
            int: 处理的通知数量
        """
        now = datetime.utcnow()
        
        # 查询需要发送的定时通知
        result = await db.execute(
            select(Notification)
            .where(
                and_(
                    Notification.status == NotificationStatus.PENDING,
                    Notification.scheduled_at.isnot(None),
                    Notification.scheduled_at <= now,
                    or_(
                        Notification.expires_at.is_(None),
                        Notification.expires_at > now
                    )
                )
            )
            .limit(100)  # 限制批量处理数量
        )
        
        notifications = result.scalars().all()
        processed_count = 0
        
        for notification in notifications:
            try:
                await self._process_notification(db, notification)
                processed_count += 1
            except Exception as e:
                logger.error(f"Failed to process scheduled notification {notification.id}: {str(e)}")
        
        logger.info(f"Processed {processed_count} scheduled notifications")
        return processed_count
    
    async def expire_notifications(self, db: AsyncSession) -> int:
        """
        处理过期通知
        
        Args:
            db: 数据库会话
            
        Returns:
            int: 过期的通知数量
        """
        now = datetime.utcnow()
        
        # 更新过期通知状态
        result = await db.execute(
            update(Notification)
            .where(
                and_(
                    Notification.status.in_([
                        NotificationStatus.PENDING,
                        NotificationStatus.FAILED
                    ]),
                    Notification.expires_at.isnot(None),
                    Notification.expires_at < now
                )
            )
            .values(
                status=NotificationStatus.EXPIRED,
                updated_at=now
            )
        )
        
        await db.commit()
        expired_count = result.rowcount
        
        logger.info(f"Expired {expired_count} notifications")
        return expired_count
    
    async def _process_notification(self, db: AsyncSession, notification: Notification):
        """
        处理单个通知
        
        Args:
            db: 数据库会话
            notification: 通知对象
        """
        logger.info(f"[{notification.id}] 开始处理通知: title={notification.title}, channels={notification.channels}")
        try:
            # 检查是否过期
            logger.info(f"[{notification.id}] 检查通知是否过期")
            if notification.expires_at and notification.expires_at < datetime.utcnow():
                logger.warning(f"[{notification.id}] 通知已过期，expires_at={notification.expires_at}")
                await self.update_notification_status(
                    db,
                    notification.id,
                    NotificationStatusUpdate(
                        status=NotificationStatus.EXPIRED,
                        error_message="Notification expired"
                    )
                )
                return
            logger.info(f"[{notification.id}] 通知未过期，继续处理")
            
            # 渲染模板（如果使用模板）
            if notification.template_id:
                logger.info(f"[{notification.id}] 开始渲染模板，template_id={notification.template_id}")
                rendered_content = await self.template_service.render_template(
                    db,
                    notification.template_id,
                    notification.template_data
                )
                notification.content = rendered_content.get("content", notification.content)
                if "subject" in rendered_content:
                    notification.title = rendered_content["subject"]
                logger.info(f"[{notification.id}] 模板渲染完成")
            else:
                logger.info(f"[{notification.id}] 无需渲染模板，直接使用原始内容")
            
            # 发送通知到所有指定渠道
            channels = notification.channels.split(',') if notification.channels else []
            logger.info(f"[{notification.id}] 准备发送到渠道: {channels}")
            success = True
            
            for channel_name in channels:
                logger.info(f"[{notification.id}] 开始处理渠道: {channel_name.strip()}")
                try:
                    # 获取渠道信息
                    logger.info(f"[{notification.id}] 获取渠道信息: {channel_name.strip()}")
                    channel = await self.channel_service.get_channel_by_name(db, channel_name.strip())
                    if not channel:
                        logger.error(f"[{notification.id}] 渠道 {channel_name} 未找到")
                        success = False
                        continue
                    logger.info(f"[{notification.id}] 渠道信息获取成功: {channel.name}, type={channel.type}")
                    
                    # 发送到该渠道
                    logger.info(f"[{notification.id}] 开始发送通知到渠道: {channel_name}")
                    result = await self.sender_service.send_notification(db, notification, channel)
                    logger.info(f"[{notification.id}] 渠道 {channel_name} 发送结果: {result}")
                    if not result.get('success', False):
                        success = False
                        logger.error(f"[{notification.id}] 发送失败 via {channel_name}: {result.get('error', 'Unknown error')}")
                    else:
                        logger.info(f"[{notification.id}] 发送成功 via {channel_name}")
                        
                except Exception as e:
                    import traceback
                    logger.error(f"[{notification.id}] 渠道 {channel_name} 发送异常: {str(e)}")
                    logger.error(f"[{notification.id}] 完整异常信息: {traceback.format_exc()}")
                    success = False
            
            if success:
                logger.info(f"[{notification.id}] 所有渠道发送成功，更新状态为SENT")
                await self.update_notification_status(
                    db,
                    notification.id,
                    NotificationStatusUpdate(status=NotificationStatus.SENT)
                )
                logger.info(f"[{notification.id}] 通知处理完成")
            else:
                # 增加重试次数
                notification.retry_attempts += 1
                logger.warning(f"[{notification.id}] 发送失败，重试次数: {notification.retry_attempts}/{notification.max_retry_attempts}")
                
                if notification.retry_attempts >= notification.max_retry_attempts:
                    logger.error(f"[{notification.id}] 达到最大重试次数，标记为失败")
                    await self.update_notification_status(
                        db,
                        notification.id,
                        NotificationStatusUpdate(
                            status=NotificationStatus.FAILED,
                            error_message="Maximum retry attempts exceeded"
                        )
                    )
                else:
                    logger.info(f"[{notification.id}] 安排重试")
                    await self.update_notification_status(
                        db,
                        notification.id,
                        NotificationStatusUpdate(
                            status=NotificationStatus.FAILED,
                            error_message="Send failed, will retry"
                        )
                    )
                    
                    # 安排重试
                    retry_delay = config.NOTIFICATION_RETRY_DELAY_SECONDS * (2 ** (notification.retry_attempts - 1))
                    logger.info(f"[{notification.id}] 等待 {retry_delay} 秒后重试")
                    await asyncio.sleep(retry_delay)
                    await self._process_notification(db, notification)
            
        except Exception as e:
            import traceback
            logger.error(f"[{notification.id}] 处理通知时发生异常: {str(e)}")
            logger.error(f"[{notification.id}] 异常详情: {traceback.format_exc()}")
            await self.update_notification_status(
                db,
                notification.id,
                NotificationStatusUpdate(
                    status=NotificationStatus.FAILED,
                    error_message=str(e)
                )
            )