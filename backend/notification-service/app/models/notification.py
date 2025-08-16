#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 通知模型

定义通知相关的数据库模型
"""

import uuid
import enum
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    String, Integer, DateTime, Boolean, Text, Enum, JSON,
    ForeignKey, Index, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from ..core.database import Base


class NotificationStatus(str, enum.Enum):
    """
    通知状态枚举
    """
    PENDING = "pending"          # 待发送
    SENDING = "sending"          # 发送中
    SENT = "sent"                # 已发送
    DELIVERED = "delivered"      # 已送达
    READ = "read"                # 已读
    FAILED = "failed"            # 发送失败
    CANCELLED = "cancelled"      # 已取消


class NotificationPriority(str, enum.Enum):
    """
    通知优先级枚举
    """
    LOW = "low"                  # 低优先级
    NORMAL = "normal"            # 普通优先级
    HIGH = "high"                # 高优先级
    URGENT = "urgent"            # 紧急
    CRITICAL = "critical"        # 严重


class NotificationCategory(str, enum.Enum):
    """
    通知分类枚举
    """
    SYSTEM = "system"            # 系统通知
    TRADING = "trading"          # 交易通知
    STRATEGY = "strategy"        # 策略通知
    ALERT = "alert"              # 告警通知
    MARKETING = "marketing"      # 营销通知
    SECURITY = "security"        # 安全通知
    MAINTENANCE = "maintenance"  # 维护通知


class Notification(Base):
    """
    通知模型
    
    存储通知的完整信息和状态
    """
    __tablename__ = "notifications"
    
    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="通知ID"
    )
    
    # 用户信息
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="用户ID（为空表示系统广播）"
    )
    
    # 通知基本信息
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="通知标题"
    )
    
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="通知内容"
    )
    
    summary: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="通知摘要"
    )
    
    # 通知分类和优先级
    category: Mapped[NotificationCategory] = mapped_column(
        Enum(NotificationCategory),
        nullable=False,
        default=NotificationCategory.SYSTEM,
        comment="通知分类"
    )
    
    priority: Mapped[NotificationPriority] = mapped_column(
        Enum(NotificationPriority),
        nullable=False,
        default=NotificationPriority.NORMAL,
        comment="通知优先级"
    )
    
    # 通知状态
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus),
        nullable=False,
        default=NotificationStatus.PENDING,
        comment="通知状态"
    )
    
    # 发送渠道
    channels: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="发送渠道列表（逗号分隔）"
    )
    
    # 模板信息
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("notification_templates.id", ondelete="SET NULL"),
        nullable=True,
        comment="模板ID"
    )
    
    template_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="模板数据"
    )
    
    # 收件人信息
    recipient_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="收件人邮箱"
    )
    
    recipient_phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="收件人手机号"
    )
    
    recipient_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="收件人扩展数据"
    )
    
    # 发送配置
    send_immediately: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否立即发送"
    )
    
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="计划发送时间"
    )
    
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="过期时间"
    )
    
    # 重试配置
    max_retry_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        comment="最大重试次数"
    )
    
    retry_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="已重试次数"
    )
    
    retry_delay_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=60,
        comment="重试延迟时间（秒）"
    )
    
    # 时间信息
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间"
    )
    
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="发送时间"
    )
    
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="送达时间"
    )
    
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="阅读时间"
    )
    
    # 错误信息
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息"
    )
    
    error_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="错误代码"
    )
    
    # 元数据
    meta_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="元数据"
    )
    
    # 关联关系
    template = relationship("NotificationTemplate", back_populates="notifications")
    
    # 表约束
    __table_args__ = (
        # 检查约束
        CheckConstraint('max_retry_attempts >= 0', name='ck_notification_max_retry_non_negative'),
        CheckConstraint('retry_attempts >= 0', name='ck_notification_retry_attempts_non_negative'),
        CheckConstraint('retry_attempts <= max_retry_attempts', name='ck_notification_retry_le_max'),
        CheckConstraint('retry_delay_seconds > 0', name='ck_notification_retry_delay_positive'),
        
        # 索引
        Index('idx_notification_user_id', 'user_id'),
        Index('idx_notification_status', 'status'),
        Index('idx_notification_category', 'category'),
        Index('idx_notification_priority', 'priority'),
        Index('idx_notification_created_at', 'created_at'),
        Index('idx_notification_scheduled_at', 'scheduled_at'),
        Index('idx_notification_user_status', 'user_id', 'status'),
        Index('idx_notification_user_category', 'user_id', 'category'),
        Index('idx_notification_template_id', 'template_id'),
        Index('idx_notification_recipient_email', 'recipient_email'),
    )
    
    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, title={self.title}, status={self.status})>"
    
    @property
    def is_pending(self) -> bool:
        """
        检查通知是否待发送
        
        Returns:
            bool: 通知是否待发送
        """
        return self.status == NotificationStatus.PENDING
    
    @property
    def is_sent(self) -> bool:
        """
        检查通知是否已发送
        
        Returns:
            bool: 通知是否已发送
        """
        return self.status in [
            NotificationStatus.SENT,
            NotificationStatus.DELIVERED,
            NotificationStatus.READ
        ]
    
    @property
    def is_failed(self) -> bool:
        """
        检查通知是否发送失败
        
        Returns:
            bool: 通知是否发送失败
        """
        return self.status == NotificationStatus.FAILED
    
    @property
    def can_retry(self) -> bool:
        """
        检查通知是否可以重试
        
        Returns:
            bool: 通知是否可以重试
        """
        return (
            self.is_failed and 
            self.retry_attempts < self.max_retry_attempts
        )
    
    @property
    def is_expired(self) -> bool:
        """
        检查通知是否已过期
        
        Returns:
            bool: 通知是否已过期
        """
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def channel_list(self) -> list:
        """
        获取发送渠道列表
        
        Returns:
            list: 发送渠道列表
        """
        if not self.channels:
            return []
        return [channel.strip() for channel in self.channels.split(',') if channel.strip()]
    
    def add_channel(self, channel: str):
        """
        添加发送渠道
        
        Args:
            channel: 渠道名称
        """
        channels = self.channel_list
        if channel not in channels:
            channels.append(channel)
            self.channels = ','.join(channels)
    
    def remove_channel(self, channel: str):
        """
        移除发送渠道
        
        Args:
            channel: 渠道名称
        """
        channels = self.channel_list
        if channel in channels:
            channels.remove(channel)
            self.channels = ','.join(channels) if channels else None