#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 通知服务API模式

定义通知服务的所有API请求和响应模式
"""

from .notification import (
    NotificationCreate,
    NotificationUpdate,
    NotificationResponse,
    NotificationListResponse,
    NotificationBatchCreate,
    NotificationBatchResponse,
    NotificationStatusUpdate,
    NotificationFilter
)

from .template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateListResponse,
    TemplateRender,
    TemplateRenderResponse,
    TemplateClone,
    TemplatePreview
)

from .channel import (
    ChannelCreate,
    ChannelUpdate,
    ChannelResponse,
    ChannelListResponse,
    ChannelTest,
    ChannelTestResponse,
    ChannelStats,
    ChannelStatsResponse
)

from .common import (
    BaseResponse,
    PaginationParams,
    PaginatedResponse,
    HealthResponse,
    ErrorResponse
)

__all__ = [
    # Notification schemas
    "NotificationCreate",
    "NotificationUpdate",
    "NotificationResponse",
    "NotificationListResponse",
    "NotificationBatchCreate",
    "NotificationBatchResponse",
    "NotificationStatusUpdate",
    "NotificationFilter",
    
    # Template schemas
    "TemplateCreate",
    "TemplateUpdate",
    "TemplateResponse",
    "TemplateListResponse",
    "TemplateRender",
    "TemplateRenderResponse",
    "TemplateClone",
    "TemplatePreview",
    
    # Channel schemas
    "ChannelCreate",
    "ChannelUpdate",
    "ChannelResponse",
    "ChannelListResponse",
    "ChannelTest",
    "ChannelTestResponse",
    "ChannelStats",
    "ChannelStatsResponse",
    
    # Common schemas
    "BaseResponse",
    "PaginationParams",
    "PaginatedResponse",
    "HealthResponse",
    "ErrorResponse"
]