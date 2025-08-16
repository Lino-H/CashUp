#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 通知服务业务逻辑层

定义通知服务的所有业务逻辑服务
"""

from .notification_service import NotificationService
from .template_service import TemplateService
from .channel_service import ChannelService
from .sender_service import SenderService
from .websocket_service import WebSocketService
from .scheduler_service import SchedulerService

# 创建服务实例 - 按依赖顺序创建
template_service = TemplateService()
channel_service = ChannelService()
sender_service = SenderService()
websocket_service = WebSocketService()
scheduler_service = SchedulerService()

# 创建需要依赖注入的服务
notification_service = NotificationService(
    template_service=template_service,
    channel_service=channel_service,
    sender_service=sender_service,
    websocket_service=websocket_service
)

__all__ = [
    "NotificationService",
    "TemplateService",
    "ChannelService",
    "SenderService",
    "WebSocketService",
    "SchedulerService",
    "notification_service",
    "template_service",
    "channel_service",
    "sender_service",
    "websocket_service",
    "scheduler_service"
]