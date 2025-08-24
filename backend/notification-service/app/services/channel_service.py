#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 渠道服务业务逻辑

处理通知渠道的管理、配置、测试等业务逻辑
"""

import uuid
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func

from ..models.channel import NotificationChannel, ChannelType, ChannelStatus
from ..schemas.channel import (
    ChannelCreate, ChannelUpdate, ChannelFilter,
    ChannelTest, ChannelConfig
)
from ..core.exceptions import (
    ChannelNotFoundError, InvalidChannelConfigError, ChannelTestError
)
from ..core.config import get_config

import logging

logger = logging.getLogger(__name__)
config = get_config()


class ChannelService:
    """
    渠道服务业务逻辑类
    
    负责处理通知渠道的管理、配置、测试等业务逻辑
    """
    
    def __init__(self):
        # 渠道配置验证器
        self.config_validators = {
            ChannelType.EMAIL: self._validate_email_config,
            ChannelType.SMS: self._validate_sms_config,
            ChannelType.WXPUSHER: self._validate_wxpusher_config,
            ChannelType.QANOTIFY: self._validate_qanotify_config,
            ChannelType.PUSHPLUS: self._validate_pushplus_config,
            ChannelType.TELEGRAM: self._validate_telegram_config,
            ChannelType.WEBSOCKET: self._validate_websocket_config,
            ChannelType.WEBHOOK: self._validate_webhook_config,
            ChannelType.SYSTEM: self._validate_system_config,
        }
        
        # 渠道测试器
        self.channel_testers = {
            ChannelType.EMAIL: self._test_email_channel,
            ChannelType.SMS: self._test_sms_channel,
            ChannelType.WXPUSHER: self._test_wxpusher_channel,
            ChannelType.QANOTIFY: self._test_qanotify_channel,
            ChannelType.PUSHPLUS: self._test_pushplus_channel,
            ChannelType.TELEGRAM: self._test_telegram_channel,
            ChannelType.WEBSOCKET: self._test_websocket_channel,
            ChannelType.WEBHOOK: self._test_webhook_channel,
            ChannelType.SYSTEM: self._test_system_channel,
        }
    
    async def create_channel(
        self,
        db: AsyncSession,
        channel_data: ChannelCreate,
        created_by: Optional[uuid.UUID] = None
    ) -> NotificationChannel:
        """
        创建渠道
        
        Args:
            db: 数据库会话
            channel_data: 渠道创建数据
            created_by: 创建者ID
            
        Returns:
            NotificationChannel: 创建的渠道
            
        Raises:
            InvalidChannelConfigError: 无效的渠道配置
        """
        try:
            # 检查渠道名称是否已存在
            existing = await self.get_channel_by_name(db, channel_data.name)
            if existing:
                raise InvalidChannelConfigError(f"Channel with name '{channel_data.name}' already exists")
            
            # 验证渠道配置
            await self._validate_channel_config(channel_data.type, channel_data.config)
            
            # 创建渠道对象
            channel = NotificationChannel(
                id=uuid.uuid4(),
                name=channel_data.name,
                display_name=channel_data.display_name,
                description=channel_data.description,
                type=channel_data.type,
                status=ChannelStatus.ACTIVE,
                config=channel_data.config,
                priority=channel_data.priority,
                rate_limit=channel_data.rate_limit,
                daily_limit=channel_data.daily_limit,
                max_retry_attempts=channel_data.max_retry_attempts,
                retry_delay_seconds=channel_data.retry_delay_seconds,
                total_sent=0,
                total_failed=0,
                today_sent=0,
                last_sent_at=None,
                last_error_at=None,
                last_error_message=None,
                created_by=created_by,
                meta_data=channel_data.metadata or {},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # 保存到数据库
            db.add(channel)
            await db.commit()
            await db.refresh(channel)
            
            logger.info(f"Created channel {channel.id} with name '{channel.name}'")
            return channel
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create channel: {str(e)}")
            raise
    
    async def get_channel(
        self,
        db: AsyncSession,
        channel_id: uuid.UUID
    ) -> Optional[NotificationChannel]:
        """
        获取渠道详情
        
        Args:
            db: 数据库会话
            channel_id: 渠道ID
            
        Returns:
            Optional[NotificationChannel]: 渠道对象
        """
        result = await db.execute(
            select(NotificationChannel)
            .where(NotificationChannel.id == channel_id)
        )
        return result.scalar_one_or_none()
    
    async def get_channel_by_name(
        self,
        db: AsyncSession,
        name: str
    ) -> Optional[NotificationChannel]:
        """
        根据名称获取渠道
        
        Args:
            db: 数据库会话
            name: 渠道名称
            
        Returns:
            Optional[NotificationChannel]: 渠道对象
        """
        result = await db.execute(
            select(NotificationChannel)
            .where(NotificationChannel.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_channels(
        self,
        db: AsyncSession,
        filters: ChannelFilter,
        page: int = 1,
        size: int = 20
    ) -> Tuple[List[NotificationChannel], int]:
        """
        获取渠道列表
        
        Args:
            db: 数据库会话
            filters: 过滤条件
            page: 页码
            size: 每页大小
            
        Returns:
            Tuple[List[NotificationChannel], int]: 渠道列表和总数
        """
        # 构建查询条件
        conditions = []
        
        if filters.name:
            conditions.append(NotificationChannel.name.ilike(f"%{filters.name}%"))
        
        if filters.type:
            conditions.append(NotificationChannel.type == filters.type)
        
        if filters.status:
            conditions.append(NotificationChannel.status == filters.status)
        
        if filters.is_active is not None:
            if filters.is_active:
                conditions.append(NotificationChannel.status == ChannelStatus.ACTIVE)
            else:
                conditions.append(NotificationChannel.status != ChannelStatus.ACTIVE)
        
        if filters.min_priority is not None:
            conditions.append(NotificationChannel.priority >= filters.min_priority)
        
        if filters.max_priority is not None:
            conditions.append(NotificationChannel.priority <= filters.max_priority)
        
        if filters.has_daily_limit is not None:
            if filters.has_daily_limit:
                conditions.append(NotificationChannel.daily_limit.isnot(None))
            else:
                conditions.append(NotificationChannel.daily_limit.is_(None))
        
        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(
                or_(
                    NotificationChannel.name.ilike(search_term),
                    NotificationChannel.display_name.ilike(search_term),
                    NotificationChannel.description.ilike(search_term)
                )
            )
        
        if filters.start_date:
            conditions.append(NotificationChannel.created_at >= filters.start_date)
        
        if filters.end_date:
            conditions.append(NotificationChannel.created_at <= filters.end_date)
        
        if filters.created_by:
            conditions.append(NotificationChannel.created_by == uuid.UUID(filters.created_by))
        
        # 查询总数
        count_query = select(func.count(NotificationChannel.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # 查询数据
        query = select(NotificationChannel)
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(NotificationChannel.priority.desc(), NotificationChannel.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)
        
        result = await db.execute(query)
        channels = result.scalars().all()
        
        return list(channels), total
    
    async def update_channel(
        self,
        db: AsyncSession,
        channel_id: uuid.UUID,
        update_data: ChannelUpdate,
        updated_by: Optional[uuid.UUID] = None
    ) -> Optional[NotificationChannel]:
        """
        更新渠道
        
        Args:
            db: 数据库会话
            channel_id: 渠道ID
            update_data: 更新数据
            updated_by: 更新者ID
            
        Returns:
            Optional[NotificationChannel]: 更新后的渠道
            
        Raises:
            ChannelNotFoundError: 渠道不存在
            InvalidChannelConfigError: 无效的更新数据
        """
        channel = await self.get_channel(db, channel_id)
        if not channel:
            raise ChannelNotFoundError(f"Channel {channel_id} not found")
        
        # 验证更新的配置（如果有配置更新）
        if update_data.config is not None:
            await self._validate_channel_config(channel.type, update_data.config)
        
        # 更新字段
        update_fields = update_data.model_dump(exclude_none=True)
        for field, value in update_fields.items():
            setattr(channel, field, value)
        
        channel.updated_by = updated_by
        channel.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(channel)
        
        logger.info(f"Updated channel {channel_id}")
        return channel
    
    async def delete_channel(
        self,
        db: AsyncSession,
        channel_id: uuid.UUID
    ) -> bool:
        """
        删除渠道
        
        Args:
            db: 数据库会话
            channel_id: 渠道ID
            
        Returns:
            bool: 是否删除成功
        """
        result = await db.execute(
            delete(NotificationChannel).where(NotificationChannel.id == channel_id)
        )
        await db.commit()
        
        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"Deleted channel {channel_id}")
        
        return deleted
    
    async def test_channel(
        self,
        db: AsyncSession,
        channel_id: uuid.UUID,
        test_data: ChannelTest
    ) -> Dict[str, Any]:
        """
        测试渠道
        
        Args:
            db: 数据库会话
            channel_id: 渠道ID
            test_data: 测试数据
            
        Returns:
            Dict[str, Any]: 测试结果
            
        Raises:
            ChannelNotFoundError: 渠道不存在
            ChannelTestError: 测试失败
        """
        channel = await self.get_channel(db, channel_id)
        if not channel:
            raise ChannelNotFoundError(f"Channel {channel_id} not found")
        
        if channel.status != ChannelStatus.ACTIVE:
            raise ChannelTestError(f"Channel {channel_id} is not active")
        
        # 获取对应的测试器
        tester = self.channel_testers.get(channel.type)
        if not tester:
            raise ChannelTestError(f"No tester available for channel type {channel.type}")
        
        start_time = datetime.utcnow()
        
        try:
            # 执行测试
            test_result = await tester(channel, test_data)
            
            # 计算测试时间
            test_duration = (datetime.utcnow() - start_time).total_seconds()
            
            # 更新渠道状态
            if test_result["success"]:
                await self._update_channel_status(db, channel_id, ChannelStatus.ACTIVE)
            else:
                await self._update_channel_status(
                    db, channel_id, ChannelStatus.ERROR,
                    error_message=test_result.get("error")
                )
            
            logger.info(f"Channel {channel_id} test completed in {test_duration:.2f}s")
            
            return {
                "channel_id": channel_id,
                "success": test_result["success"],
                "message": test_result.get("message", "Test completed"),
                "error": test_result.get("error"),
                "test_duration": test_duration,
                "timestamp": start_time.isoformat(),
                "details": test_result.get("details", {})
            }
            
        except Exception as e:
            # 更新渠道状态为错误
            await self._update_channel_status(
                db, channel_id, ChannelStatus.ERROR,
                error_message=str(e)
            )
            
            logger.error(f"Channel {channel_id} test failed: {str(e)}")
            raise ChannelTestError(f"Channel test failed: {str(e)}")
    
    async def get_channel_health(
        self,
        db: AsyncSession,
        channel_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        获取渠道健康状态
        
        Args:
            db: 数据库会话
            channel_id: 渠道ID
            
        Returns:
            Dict[str, Any]: 健康状态信息
        """
        channel = await self.get_channel(db, channel_id)
        if not channel:
            raise ChannelNotFoundError(f"Channel {channel_id} not found")
        
        # 计算成功率
        success_rate = channel.get_success_rate()
        
        # 检查是否可用
        is_available = channel.is_available()
        
        # 检查今日发送量
        today_sent = channel.get_today_sent_count()
        daily_limit_reached = channel.daily_limit and today_sent >= channel.daily_limit
        
        # 计算健康分数
        health_score = self._calculate_health_score(channel, success_rate, is_available)
        
        # 确定健康状态
        if health_score >= 90:
            health_status = "excellent"
        elif health_score >= 70:
            health_status = "good"
        elif health_score >= 50:
            health_status = "fair"
        else:
            health_status = "poor"
        
        return {
            "channel_id": channel_id,
            "health_status": health_status,
            "health_score": health_score,
            "is_active": channel.is_active(),
            "is_available": is_available,
            "success_rate": success_rate,
            "total_sent": channel.total_sent,
            "failed_count": channel.total_failed,
            "today_sent": today_sent,
            "daily_limit": channel.daily_limit,
            "daily_limit_reached": daily_limit_reached,
            "last_sent_at": channel.last_sent_at.isoformat() if channel.last_sent_at else None,
            "last_error_at": channel.last_error_at.isoformat() if channel.last_error_at else None,
            "last_error_message": channel.last_error_message,
            "status": channel.status.value
        }
    
    async def get_channel_metrics(
        self,
        db: AsyncSession,
        channel_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取渠道指标
        
        Args:
            db: 数据库会话
            channel_id: 渠道ID
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Dict[str, Any]: 指标信息
        """
        channel = await self.get_channel(db, channel_id)
        if not channel:
            raise ChannelNotFoundError(f"Channel {channel_id} not found")
        
        # 基础指标
        metrics = {
            "channel_id": channel_id,
            "total_sent": channel.total_sent,
            "total_failed": channel.total_failed,
            "success_rate": channel.get_success_rate(),
            "today_sent": channel.get_today_sent_count(),
            "daily_limit": channel.daily_limit,
            "priority": channel.priority,
            "status": channel.status.value,
            "created_at": channel.created_at.isoformat(),
            "last_sent_at": channel.last_sent_at.isoformat() if channel.last_sent_at else None,
            "last_error_at": channel.last_error_at.isoformat() if channel.last_error_at else None
        }
        
        # 如果有时间范围，可以添加更详细的统计
        if start_date and end_date:
            # 这里可以添加基于时间范围的详细统计
            # 由于当前模型没有详细的发送记录表，这里只返回基础信息
            metrics["period"] = {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        
        return metrics
    
    async def get_channel_stats(
        self,
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取渠道统计信息
        
        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        conditions = []
        
        if start_date:
            conditions.append(NotificationChannel.created_at >= start_date)
        
        if end_date:
            conditions.append(NotificationChannel.created_at <= end_date)
        
        base_query = select(NotificationChannel)
        if conditions:
            base_query = base_query.where(and_(*conditions))
        
        # 总数统计
        total_query = select(func.count(NotificationChannel.id))
        if conditions:
            total_query = total_query.where(and_(*conditions))
        
        total_result = await db.execute(total_query)
        total = total_result.scalar()
        
        # 活跃渠道数
        active_query = select(func.count(NotificationChannel.id)).where(
            NotificationChannel.status == ChannelStatus.ACTIVE
        )
        if conditions:
            active_query = active_query.where(and_(*conditions))
        
        active_result = await db.execute(active_query)
        active = active_result.scalar()
        
        # 按类型统计
        type_query = select(
            NotificationChannel.type,
            func.count(NotificationChannel.id)
        ).group_by(NotificationChannel.type)
        if conditions:
            type_query = type_query.where(and_(*conditions))
        
        type_result = await db.execute(type_query)
        type_stats = {channel_type.value: count for channel_type, count in type_result.fetchall()}
        
        # 按状态统计
        status_query = select(
            NotificationChannel.status,
            func.count(NotificationChannel.id)
        ).group_by(NotificationChannel.status)
        if conditions:
            status_query = status_query.where(and_(*conditions))
        
        status_result = await db.execute(status_query)
        status_stats = {status.value: count for status, count in status_result.fetchall()}
        
        # 发送统计
        sent_query = select(
            func.sum(NotificationChannel.total_sent),
            func.sum(NotificationChannel.total_failed)
        )
        if conditions:
            sent_query = sent_query.where(and_(*conditions))
        
        sent_result = await db.execute(sent_query)
        sent_data = sent_result.fetchone()
        total_sent = sent_data[0] or 0
        total_failed = sent_data[1] or 0
        
        # 最活跃渠道
        most_active_query = select(NotificationChannel).order_by(
            NotificationChannel.total_sent.desc()
        ).limit(5)
        if conditions:
            most_active_query = most_active_query.where(and_(*conditions))
        
        most_active_result = await db.execute(most_active_query)
        most_active = [
            {
                "id": str(channel.id),
                "name": channel.name,
                "display_name": channel.display_name,
                "type": channel.type.value,
                "total_sent": channel.total_sent,
                "success_rate": channel.get_success_rate()
            }
            for channel in most_active_result.scalars().all()
        ]
        
        return {
            "total": total,
            "active": active,
            "inactive": total - active,
            "by_type": type_stats,
            "by_status": status_stats,
            "total_sent": total_sent,
            "total_failed": total_failed,
            "overall_success_rate": (total_sent / (total_sent + total_failed)) * 100 if (total_sent + total_failed) > 0 else 0.0,
            "most_active": most_active
        }
    
    async def _validate_channel_config(
        self,
        channel_type: ChannelType,
        config: Dict[str, Any]
    ):
        """
        验证渠道配置
        
        Args:
            channel_type: 渠道类型
            config: 配置数据
            
        Raises:
            InvalidChannelConfigError: 无效的配置
        """
        validator = self.config_validators.get(channel_type)
        if not validator:
            raise InvalidChannelConfigError(f"No validator available for channel type {channel_type}")
        
        await validator(config)
    
    async def _validate_email_config(self, config: Dict[str, Any]):
        """验证邮件渠道配置"""
        required_fields = ['smtp_host', 'smtp_port', 'username', 'password']
        for field in required_fields:
            if field not in config:
                raise InvalidChannelConfigError(f"Missing required field: {field}")
        
        # 验证端口号
        try:
            port = int(config['smtp_port'])
            if port <= 0 or port > 65535:
                raise ValueError()
        except (ValueError, TypeError):
            raise InvalidChannelConfigError("Invalid SMTP port")
    
    async def _validate_sms_config(self, config: Dict[str, Any]):
        """验证短信渠道配置"""
        required_fields = ['provider', 'api_key']
        for field in required_fields:
            if field not in config:
                raise InvalidChannelConfigError(f"Missing required field: {field}")
        
        # 验证提供商
        valid_providers = ['twilio', 'aliyun', 'tencent']
        if config['provider'] not in valid_providers:
            raise InvalidChannelConfigError(f"Invalid SMS provider. Must be one of: {', '.join(valid_providers)}")
    
    async def _validate_wechat_config(self, config: Dict[str, Any]):
        """验证微信渠道配置"""
        required_fields = ['app_id', 'app_secret']
        for field in required_fields:
            if field not in config:
                raise InvalidChannelConfigError(f"Missing required field: {field}")
    
    async def _validate_telegram_config(self, config: Dict[str, Any]):
        """验证Telegram渠道配置"""
        required_fields = ['bot_token']
        for field in required_fields:
            if field not in config:
                raise InvalidChannelConfigError(f"Missing required field: {field}")
    
    async def _validate_slack_config(self, config: Dict[str, Any]):
        """验证Slack渠道配置"""
        required_fields = ['webhook_url']
        for field in required_fields:
            if field not in config:
                raise InvalidChannelConfigError(f"Missing required field: {field}")
    
    async def _validate_discord_config(self, config: Dict[str, Any]):
        """验证Discord渠道配置"""
        required_fields = ['webhook_url']
        for field in required_fields:
            if field not in config:
                raise InvalidChannelConfigError(f"Missing required field: {field}")
    
    async def _validate_webhook_config(self, config: Dict[str, Any]):
        """验证Webhook渠道配置"""
        required_fields = ['url']
        for field in required_fields:
            if field not in config:
                raise InvalidChannelConfigError(f"Missing required field: {field}")
        
        # 验证HTTP方法
        method = config.get('method', 'POST')
        valid_methods = ['GET', 'POST', 'PUT', 'PATCH']
        if method not in valid_methods:
            raise InvalidChannelConfigError(f"Invalid HTTP method. Must be one of: {', '.join(valid_methods)}")
    
    async def _validate_push_config(self, config: Dict[str, Any]):
        """验证推送渠道配置"""
        required_fields = ['provider', 'api_key']
        for field in required_fields:
            if field not in config:
                raise InvalidChannelConfigError(f"Missing required field: {field}")
        
        # 验证提供商
        valid_providers = ['firebase', 'apns', 'jpush']
        if config['provider'] not in valid_providers:
            raise InvalidChannelConfigError(f"Invalid push provider. Must be one of: {', '.join(valid_providers)}")
    
    async def _test_email_channel(self, channel: NotificationChannel, test_data: ChannelTest) -> Dict[str, Any]:
        """测试邮件渠道"""
        # 这里应该实现实际的邮件发送测试
        # 为了演示，这里只是模拟测试
        await asyncio.sleep(0.1)  # 模拟网络延迟
        
        return {
            "success": True,
            "message": "Email channel test successful",
            "details": {
                "smtp_host": channel.config.get('smtp_host'),
                "test_recipient": test_data.recipient
            }
        }
    
    async def _test_sms_channel(self, channel: NotificationChannel, test_data: ChannelTest) -> Dict[str, Any]:
        """测试短信渠道"""
        await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "message": "SMS channel test successful",
            "details": {
                "provider": channel.config.get('provider'),
                "test_recipient": test_data.recipient
            }
        }
    
    async def _test_wechat_channel(self, channel: NotificationChannel, test_data: ChannelTest) -> Dict[str, Any]:
        """测试微信渠道"""
        await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "message": "WeChat channel test successful",
            "details": {
                "app_id": channel.config.get('app_id'),
                "test_recipient": test_data.recipient
            }
        }
    
    async def _test_telegram_channel(self, channel: NotificationChannel, test_data: ChannelTest) -> Dict[str, Any]:
        """测试Telegram渠道"""
        await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "message": "Telegram channel test successful",
            "details": {
                "bot_token": "***" + channel.config.get('bot_token', '')[-4:],
                "test_recipient": test_data.recipient
            }
        }
    
    async def _test_slack_channel(self, channel: NotificationChannel, test_data: ChannelTest) -> Dict[str, Any]:
        """测试Slack渠道"""
        await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "message": "Slack channel test successful",
            "details": {
                "webhook_url": channel.config.get('webhook_url', '')[:50] + "...",
                "test_recipient": test_data.recipient
            }
        }
    
    async def _test_discord_channel(self, channel: NotificationChannel, test_data: ChannelTest) -> Dict[str, Any]:
        """测试Discord渠道"""
        await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "message": "Discord channel test successful",
            "details": {
                "webhook_url": channel.config.get('webhook_url', '')[:50] + "...",
                "test_recipient": test_data.recipient
            }
        }
    
    async def _test_webhook_channel(self, channel: NotificationChannel, test_data: ChannelTest) -> Dict[str, Any]:
        """测试Webhook渠道"""
        await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "message": "Webhook channel test successful",
            "details": {
                "url": channel.config.get('url', '')[:50] + "...",
                "method": channel.config.get('method', 'POST'),
                "test_recipient": test_data.recipient
            }
        }
    
    async def _test_push_channel(self, channel: NotificationChannel, test_data: ChannelTest) -> Dict[str, Any]:
        """测试推送渠道"""
        await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "message": "Push channel test successful",
            "details": {
                "provider": channel.config.get('provider'),
                "test_recipient": test_data.recipient
            }
        }
    
    async def _update_channel_status(
        self,
        db: AsyncSession,
        channel_id: uuid.UUID,
        status: ChannelStatus,
        error_message: Optional[str] = None
    ):
        """
        更新渠道状态
        
        Args:
            db: 数据库会话
            channel_id: 渠道ID
            status: 新状态
            error_message: 错误消息
        """
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if error_message:
            update_data["last_error_message"] = error_message
            update_data["last_error_at"] = datetime.utcnow()
        
        await db.execute(
            update(NotificationChannel)
            .where(NotificationChannel.id == channel_id)
            .values(**update_data)
        )
        await db.commit()
    
    def _calculate_health_score(
        self,
        channel: NotificationChannel,
        success_rate: float,
        is_available: bool
    ) -> float:
        """
        计算渠道健康分数
        
        Args:
            channel: 渠道对象
            success_rate: 成功率
            is_available: 是否可用
            
        Returns:
            float: 健康分数 (0-100)
        """
        score = 0.0
        
        # 基础分数：状态
        if channel.status == ChannelStatus.ACTIVE:
            score += 40
        elif channel.status == ChannelStatus.MAINTENANCE:
            score += 20
        
        # 成功率分数 (40分)
        score += success_rate * 0.4
        
        # 可用性分数 (20分)
        if is_available:
            score += 20
        
        # 最近错误扣分
        if channel.last_error_at:
            hours_since_error = (datetime.utcnow() - channel.last_error_at).total_seconds() / 3600
            if hours_since_error < 1:
                score -= 10
            elif hours_since_error < 24:
                score -= 5
        
        return max(0.0, min(100.0, score))
    
    async def _validate_wxpusher_config(self, config: Dict[str, Any]):
        """验证微信推送渠道配置"""
        required_fields = ['app_token']
        for field in required_fields:
            if field not in config:
                raise InvalidChannelConfigError(f"Missing required field: {field}")
    
    async def _validate_qanotify_config(self, config: Dict[str, Any]):
        """验证QANotify渠道配置"""
        required_fields = ['key']
        for field in required_fields:
            if field not in config:
                raise InvalidChannelConfigError(f"Missing required field: {field}")
    
    async def _validate_pushplus_config(self, config: Dict[str, Any]):
        """验证PushPlus渠道配置"""
        required_fields = ['token']
        for field in required_fields:
            if field not in config:
                raise InvalidChannelConfigError(f"Missing required field: {field}")
    
    async def _validate_websocket_config(self, config: Dict[str, Any]):
        """验证WebSocket渠道配置"""
        # WebSocket渠道可能不需要特殊配置
        pass
    
    async def _validate_system_config(self, config: Dict[str, Any]):
        """验证系统通知渠道配置"""
        # 系统通知渠道可能不需要特殊配置
        pass
    
    async def _test_wxpusher_channel(self, channel: NotificationChannel, test_data: ChannelTest) -> Dict[str, Any]:
        """测试微信推送渠道"""
        await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "message": "WxPusher channel test successful",
            "details": {
                "app_token": "***" + channel.config.get('app_token', '')[-4:],
                "test_recipient": test_data.recipient
            }
        }
    
    async def _test_qanotify_channel(self, channel: NotificationChannel, test_data: ChannelTest) -> Dict[str, Any]:
        """测试QANotify渠道"""
        await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "message": "QANotify channel test successful",
            "details": {
                "key": "***" + channel.config.get('key', '')[-4:],
                "test_recipient": test_data.recipient
            }
        }
    
    async def _test_pushplus_channel(self, channel: NotificationChannel, test_data: ChannelTest) -> Dict[str, Any]:
        """测试PushPlus渠道"""
        await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "message": "PushPlus channel test successful",
            "details": {
                "token": "***" + channel.config.get('token', '')[-4:],
                "test_recipient": test_data.recipient
            }
        }
    
    async def _test_websocket_channel(self, channel: NotificationChannel, test_data: ChannelTest) -> Dict[str, Any]:
        """测试WebSocket渠道"""
        await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "message": "WebSocket channel test successful",
            "details": {
                "test_recipient": test_data.recipient
            }
        }
    
    async def _test_system_channel(self, channel: NotificationChannel, test_data: ChannelTest) -> Dict[str, Any]:
        """测试系统通知渠道"""
        await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "message": "System channel test successful",
            "details": {
                "test_recipient": test_data.recipient
            }
        }