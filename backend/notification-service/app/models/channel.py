#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 通知渠道模型

定义通知渠道相关的数据库模型
"""

import uuid
import enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    String, Integer, DateTime, Boolean, Text, Enum, JSON,
    Index, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from ..core.database import Base


class ChannelType(str, enum.Enum):
    """
    渠道类型枚举
    """
    EMAIL = "email"              # 邮件
    SMS = "sms"                  # 短信
    WXPUSHER = "wxpusher"        # 微信推送
    QANOTIFY = "qanotify"        # QANotify
    PUSHPLUS = "pushplus"        # PushPlus
    TELEGRAM = "telegram"        # Telegram
    WEBSOCKET = "websocket"      # WebSocket
    WEBHOOK = "webhook"          # Webhook
    SYSTEM = "system"            # 系统通知


class ChannelStatus(str, enum.Enum):
    """
    渠道状态枚举
    """
    ACTIVE = "active"            # 活跃
    INACTIVE = "inactive"        # 非活跃
    ERROR = "error"              # 错误
    MAINTENANCE = "maintenance"  # 维护中
    DISABLED = "disabled"        # 已禁用


class NotificationChannel(Base):
    """
    通知渠道模型
    
    存储各种通知渠道的配置和状态
    """
    __tablename__ = "notification_channels"
    
    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="渠道ID"
    )
    
    # 渠道基本信息
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="渠道名称"
    )
    
    display_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="渠道显示名称"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="渠道描述"
    )
    
    # 渠道类型和状态
    type: Mapped[ChannelType] = mapped_column(
        Enum(ChannelType),
        nullable=False,
        comment="渠道类型"
    )
    
    status: Mapped[ChannelStatus] = mapped_column(
        Enum(ChannelStatus),
        nullable=False,
        default=ChannelStatus.ACTIVE,
        comment="渠道状态"
    )
    
    # 渠道配置
    config: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="渠道配置"
    )
    
    # 优先级和限制
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        comment="渠道优先级（数字越小优先级越高）"
    )
    
    rate_limit: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="速率限制（每分钟最大发送数）"
    )
    
    daily_limit: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="每日发送限制"
    )
    
    # 重试配置
    max_retry_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        comment="最大重试次数"
    )
    
    retry_delay_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=60,
        comment="重试延迟时间（秒）"
    )
    
    # 统计信息
    total_sent: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="总发送数"
    )
    
    total_failed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="总失败数"
    )
    
    today_sent: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="今日发送数"
    )
    
    last_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="最后发送时间"
    )
    
    last_error_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="最后错误时间"
    )
    
    last_error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="最后错误信息"
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
    
    # 创建者信息
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="创建者ID"
    )
    
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="更新者ID"
    )
    
    # 元数据
    meta_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="元数据"
    )
    
    # 表约束
    __table_args__ = (
        # 检查约束
        CheckConstraint('priority >= 0', name='ck_channel_priority_non_negative'),
        CheckConstraint('rate_limit IS NULL OR rate_limit > 0', name='ck_channel_rate_limit_positive'),
        CheckConstraint('daily_limit IS NULL OR daily_limit > 0', name='ck_channel_daily_limit_positive'),
        CheckConstraint('max_retry_attempts >= 0', name='ck_channel_max_retry_non_negative'),
        CheckConstraint('retry_delay_seconds > 0', name='ck_channel_retry_delay_positive'),
        CheckConstraint('total_sent >= 0', name='ck_channel_total_sent_non_negative'),
        CheckConstraint('total_failed >= 0', name='ck_channel_total_failed_non_negative'),
        CheckConstraint('today_sent >= 0', name='ck_channel_today_sent_non_negative'),
        
        # 索引
        Index('idx_channel_name', 'name'),
        Index('idx_channel_type', 'type'),
        Index('idx_channel_status', 'status'),
        Index('idx_channel_priority', 'priority'),
        Index('idx_channel_created_at', 'created_at'),
        Index('idx_channel_type_status', 'type', 'status'),
        Index('idx_channel_created_by', 'created_by'),
    )
    
    def __repr__(self) -> str:
        return f"<NotificationChannel(id={self.id}, name={self.name}, type={self.type})>"
    
    @property
    def is_active(self) -> bool:
        """
        检查渠道是否活跃
        
        Returns:
            bool: 渠道是否活跃
        """
        return self.status == ChannelStatus.ACTIVE
    
    @property
    def is_available(self) -> bool:
        """
        检查渠道是否可用
        
        Returns:
            bool: 渠道是否可用
        """
        return self.status in [ChannelStatus.ACTIVE, ChannelStatus.INACTIVE]
    
    @property
    def success_rate(self) -> float:
        """
        计算成功率
        
        Returns:
            float: 成功率（0-1）
        """
        if self.total_sent == 0:
            return 0.0
        return (self.total_sent - self.total_failed) / self.total_sent
    
    @property
    def can_send_today(self) -> bool:
        """
        检查今日是否还能发送
        
        Returns:
            bool: 今日是否还能发送
        """
        if not self.daily_limit:
            return True
        return self.today_sent < self.daily_limit
    
    def get_config_value(self, key: str, default=None):
        """
        获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        return self.config.get(key, default)
    
    def set_config_value(self, key: str, value):
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        if self.config is None:
            self.config = {}
        self.config[key] = value
    
    def increment_sent(self):
        """
        增加发送计数
        """
        self.total_sent += 1
        self.today_sent += 1
        self.last_sent_at = datetime.utcnow()
    
    def increment_failed(self, error_message: str = None):
        """
        增加失败计数
        
        Args:
            error_message: 错误信息
        """
        self.total_failed += 1
        self.last_error_at = datetime.utcnow()
        if error_message:
            self.last_error_message = error_message
    
    def reset_today_count(self):
        """
        重置今日计数
        """
        self.today_sent = 0
    
    def update_status(self, status: ChannelStatus, error_message: str = None):
        """
        更新渠道状态
        
        Args:
            status: 新状态
            error_message: 错误信息（如果状态为错误）
        """
        self.status = status
        if status == ChannelStatus.ERROR and error_message:
            self.last_error_at = datetime.utcnow()
            self.last_error_message = error_message
    
    def validate_config(self) -> List[str]:
        """
        验证渠道配置
        
        Returns:
            List[str]: 配置错误列表
        """
        errors = []
        
        # 根据渠道类型验证必需的配置
        if self.type == ChannelType.EMAIL:
            required_keys = ['host', 'port', 'username', 'password']
        elif self.type == ChannelType.SMS:
            required_keys = ['provider', 'access_key', 'secret_key']
        elif self.type == ChannelType.WXPUSHER:
            required_keys = ['app_token']
        elif self.type == ChannelType.QANOTIFY:
            required_keys = ['key']
        elif self.type == ChannelType.PUSHPLUS:
            required_keys = ['token']
        elif self.type == ChannelType.TELEGRAM:
            required_keys = ['bot_token']
        elif self.type == ChannelType.WEBHOOK:
            required_keys = ['url']
        else:
            required_keys = []
        
        for key in required_keys:
            if not self.get_config_value(key):
                errors.append(f"Missing required config: {key}")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            Dict[str, Any]: 渠道信息字典
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "type": self.type.value,
            "status": self.status.value,
            "priority": self.priority,
            "rate_limit": self.rate_limit,
            "daily_limit": self.daily_limit,
            "total_sent": self.total_sent,
            "total_failed": self.total_failed,
            "today_sent": self.today_sent,
            "success_rate": self.success_rate,
            "can_send_today": self.can_send_today,
            "is_active": self.is_active,
            "is_available": self.is_available,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }