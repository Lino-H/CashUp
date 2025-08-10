#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 仪表板数据模式

定义仪表板相关的API请求和响应数据模式
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class DashboardTypeEnum(str, Enum):
    """仪表板类型枚举"""
    SYSTEM = "system"
    APPLICATION = "application"
    BUSINESS = "business"
    CUSTOM = "custom"
    TEMPLATE = "template"


class WidgetTypeEnum(str, Enum):
    """组件类型枚举"""
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    AREA_CHART = "area_chart"
    SCATTER_CHART = "scatter_chart"
    GAUGE = "gauge"
    COUNTER = "counter"
    TABLE = "table"
    HEATMAP = "heatmap"
    MAP = "map"
    TEXT = "text"
    IMAGE = "image"
    IFRAME = "iframe"
    ALERT_LIST = "alert_list"
    LOG_VIEWER = "log_viewer"
    STATUS_INDICATOR = "status_indicator"
    PROGRESS_BAR = "progress_bar"
    SPARKLINE = "sparkline"
    CUSTOM = "custom"


class RefreshIntervalEnum(str, Enum):
    """刷新间隔枚举"""
    REAL_TIME = "real_time"
    FIVE_SECONDS = "5s"
    TEN_SECONDS = "10s"
    THIRTY_SECONDS = "30s"
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    TEN_MINUTES = "10m"
    THIRTY_MINUTES = "30m"
    ONE_HOUR = "1h"
    MANUAL = "manual"


class TimeRangeEnum(str, Enum):
    """时间范围枚举"""
    LAST_5_MINUTES = "5m"
    LAST_15_MINUTES = "15m"
    LAST_30_MINUTES = "30m"
    LAST_1_HOUR = "1h"
    LAST_3_HOURS = "3h"
    LAST_6_HOURS = "6h"
    LAST_12_HOURS = "12h"
    LAST_24_HOURS = "24h"
    LAST_3_DAYS = "3d"
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30d"
    CUSTOM = "custom"


# 仪表板基础模式
class DashboardBase(BaseModel):
    """仪表板基础模式"""
    title: str = Field(..., description="仪表板标题", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="仪表板描述", max_length=1000)
    dashboard_type: DashboardTypeEnum = Field(..., description="仪表板类型")
    layout: Dict[str, Any] = Field(..., description="布局配置")
    theme: Optional[str] = Field("default", description="主题", max_length=50)
    tags: Optional[List[str]] = Field(default_factory=list, description="标签")
    
    @validator('layout')
    def validate_layout(cls, v):
        """验证布局配置"""
        required_fields = ['grid', 'widgets']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'Missing required field "{field}" in layout')
        return v


class DashboardCreate(DashboardBase):
    """创建仪表板请求模式"""
    is_public: bool = Field(False, description="是否公开")
    is_template: bool = Field(False, description="是否模板")
    auto_refresh: bool = Field(True, description="是否自动刷新")
    refresh_interval: RefreshIntervalEnum = Field(RefreshIntervalEnum.ONE_MINUTE, description="刷新间隔")
    time_range: TimeRangeEnum = Field(TimeRangeEnum.LAST_1_HOUR, description="默认时间范围")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="默认过滤器")
    variables: Optional[Dict[str, Any]] = Field(default_factory=dict, description="变量定义")
    permissions: Optional[Dict[str, List[str]]] = Field(default_factory=dict, description="权限配置")


class DashboardUpdate(BaseModel):
    """更新仪表板请求模式"""
    title: Optional[str] = Field(None, description="仪表板标题", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="仪表板描述", max_length=1000)
    layout: Optional[Dict[str, Any]] = Field(None, description="布局配置")
    theme: Optional[str] = Field(None, description="主题", max_length=50)
    tags: Optional[List[str]] = Field(None, description="标签")
    is_public: Optional[bool] = Field(None, description="是否公开")
    is_template: Optional[bool] = Field(None, description="是否模板")
    auto_refresh: Optional[bool] = Field(None, description="是否自动刷新")
    refresh_interval: Optional[RefreshIntervalEnum] = Field(None, description="刷新间隔")
    time_range: Optional[TimeRangeEnum] = Field(None, description="默认时间范围")
    filters: Optional[Dict[str, Any]] = Field(None, description="默认过滤器")
    variables: Optional[Dict[str, Any]] = Field(None, description="变量定义")
    permissions: Optional[Dict[str, List[str]]] = Field(None, description="权限配置")


class DashboardResponse(DashboardBase):
    """仪表板响应模式"""
    id: int = Field(..., description="仪表板ID")
    is_public: bool = Field(..., description="是否公开")
    is_template: bool = Field(..., description="是否模板")
    auto_refresh: bool = Field(..., description="是否自动刷新")
    refresh_interval: RefreshIntervalEnum = Field(..., description="刷新间隔")
    time_range: TimeRangeEnum = Field(..., description="默认时间范围")
    filters: Dict[str, Any] = Field(default_factory=dict, description="默认过滤器")
    variables: Dict[str, Any] = Field(default_factory=dict, description="变量定义")
    permissions: Dict[str, List[str]] = Field(default_factory=dict, description="权限配置")
    owner: Optional[str] = Field(None, description="所有者")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_viewed_at: Optional[datetime] = Field(None, description="最后查看时间")
    view_count: int = Field(0, description="查看次数")
    widget_count: int = Field(0, description="组件数量")
    
    class Config:
        from_attributes = True


# 仪表板组件模式
class DashboardWidgetBase(BaseModel):
    """仪表板组件基础模式"""
    title: str = Field(..., description="组件标题", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="组件描述", max_length=500)
    widget_type: WidgetTypeEnum = Field(..., description="组件类型")
    config: Dict[str, Any] = Field(..., description="组件配置")
    position: Dict[str, int] = Field(..., description="位置信息")
    size: Dict[str, int] = Field(..., description="尺寸信息")
    
    @validator('position')
    def validate_position(cls, v):
        """验证位置信息"""
        required_fields = ['x', 'y']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'Missing required field "{field}" in position')
            if not isinstance(v[field], int) or v[field] < 0:
                raise ValueError(f'Field "{field}" must be a non-negative integer')
        return v
    
    @validator('size')
    def validate_size(cls, v):
        """验证尺寸信息"""
        required_fields = ['width', 'height']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'Missing required field "{field}" in size')
            if not isinstance(v[field], int) or v[field] <= 0:
                raise ValueError(f'Field "{field}" must be a positive integer')
        return v


class DashboardWidgetCreate(DashboardWidgetBase):
    """创建仪表板组件请求模式"""
    dashboard_id: int = Field(..., description="仪表板ID")
    data_source: Optional[str] = Field(None, description="数据源", max_length=255)
    query: Optional[str] = Field(None, description="查询语句", max_length=2000)
    refresh_interval: Optional[RefreshIntervalEnum] = Field(None, description="刷新间隔")
    time_range: Optional[TimeRangeEnum] = Field(None, description="时间范围")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="过滤器")
    variables: Optional[Dict[str, Any]] = Field(default_factory=dict, description="变量")
    styling: Optional[Dict[str, Any]] = Field(default_factory=dict, description="样式配置")
    interactions: Optional[Dict[str, Any]] = Field(default_factory=dict, description="交互配置")


class DashboardWidgetUpdate(BaseModel):
    """更新仪表板组件请求模式"""
    title: Optional[str] = Field(None, description="组件标题", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="组件描述", max_length=500)
    config: Optional[Dict[str, Any]] = Field(None, description="组件配置")
    position: Optional[Dict[str, int]] = Field(None, description="位置信息")
    size: Optional[Dict[str, int]] = Field(None, description="尺寸信息")
    data_source: Optional[str] = Field(None, description="数据源", max_length=255)
    query: Optional[str] = Field(None, description="查询语句", max_length=2000)
    refresh_interval: Optional[RefreshIntervalEnum] = Field(None, description="刷新间隔")
    time_range: Optional[TimeRangeEnum] = Field(None, description="时间范围")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤器")
    variables: Optional[Dict[str, Any]] = Field(None, description="变量")
    styling: Optional[Dict[str, Any]] = Field(None, description="样式配置")
    interactions: Optional[Dict[str, Any]] = Field(None, description="交互配置")


class DashboardWidgetResponse(DashboardWidgetBase):
    """仪表板组件响应模式"""
    id: int = Field(..., description="组件ID")
    dashboard_id: int = Field(..., description="仪表板ID")
    data_source: Optional[str] = Field(None, description="数据源")
    query: Optional[str] = Field(None, description="查询语句")
    refresh_interval: Optional[RefreshIntervalEnum] = Field(None, description="刷新间隔")
    time_range: Optional[TimeRangeEnum] = Field(None, description="时间范围")
    filters: Dict[str, Any] = Field(default_factory=dict, description="过滤器")
    variables: Dict[str, Any] = Field(default_factory=dict, description="变量")
    styling: Dict[str, Any] = Field(default_factory=dict, description="样式配置")
    interactions: Dict[str, Any] = Field(default_factory=dict, description="交互配置")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_data_update: Optional[datetime] = Field(None, description="最后数据更新时间")
    error_count: int = Field(0, description="错误次数")
    last_error: Optional[str] = Field(None, description="最后错误")
    
    class Config:
        from_attributes = True


# 仪表板配置模式
class DashboardConfigBase(BaseModel):
    """仪表板配置基础模式"""
    name: str = Field(..., description="配置名称", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="配置描述", max_length=1000)
    config_type: str = Field(..., description="配置类型", max_length=50)
    config_data: Dict[str, Any] = Field(..., description="配置数据")
    scope: str = Field("global", description="配置范围", max_length=50)
    tags: Optional[List[str]] = Field(default_factory=list, description="标签")


class DashboardConfigCreate(DashboardConfigBase):
    """创建仪表板配置请求模式"""
    is_active: bool = Field(True, description="是否激活")
    priority: int = Field(0, description="优先级", ge=0, le=100)
    environment: Optional[str] = Field(None, description="环境", max_length=50)
    version: Optional[str] = Field(None, description="版本", max_length=50)


class DashboardConfigUpdate(BaseModel):
    """更新仪表板配置请求模式"""
    name: Optional[str] = Field(None, description="配置名称", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="配置描述", max_length=1000)
    config_data: Optional[Dict[str, Any]] = Field(None, description="配置数据")
    scope: Optional[str] = Field(None, description="配置范围", max_length=50)
    tags: Optional[List[str]] = Field(None, description="标签")
    is_active: Optional[bool] = Field(None, description="是否激活")
    priority: Optional[int] = Field(None, description="优先级", ge=0, le=100)
    environment: Optional[str] = Field(None, description="环境", max_length=50)
    version: Optional[str] = Field(None, description="版本", max_length=50)


class DashboardConfigResponse(DashboardConfigBase):
    """仪表板配置响应模式"""
    id: int = Field(..., description="配置ID")
    is_active: bool = Field(..., description="是否激活")
    priority: int = Field(..., description="优先级")
    environment: Optional[str] = Field(None, description="环境")
    version: Optional[str] = Field(None, description="版本")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[str] = Field(None, description="创建者")
    updated_by: Optional[str] = Field(None, description="更新者")
    
    class Config:
        from_attributes = True


# 仪表板模板模式
class DashboardTemplateResponse(BaseModel):
    """仪表板模板响应模式"""
    id: int = Field(..., description="模板ID")
    name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    category: str = Field(..., description="模板分类")
    preview_image: Optional[str] = Field(None, description="预览图片")
    template_data: Dict[str, Any] = Field(..., description="模板数据")
    tags: List[str] = Field(default_factory=list, description="标签")
    usage_count: int = Field(0, description="使用次数")
    rating: float = Field(0.0, description="评分")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class DashboardTemplateCreateRequest(BaseModel):
    """基于模板创建仪表板请求模式"""
    template_id: int = Field(..., description="模板ID")
    title: str = Field(..., description="仪表板标题", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="仪表板描述", max_length=1000)
    customizations: Optional[Dict[str, Any]] = Field(default_factory=dict, description="自定义配置")
    variables: Optional[Dict[str, Any]] = Field(default_factory=dict, description="变量值")


# 仪表板操作请求模式
class DashboardCloneRequest(BaseModel):
    """克隆仪表板请求模式"""
    title: str = Field(..., description="新仪表板标题", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="新仪表板描述", max_length=1000)
    include_data: bool = Field(False, description="是否包含数据")
    copy_permissions: bool = Field(False, description="是否复制权限")


class DashboardShareRequest(BaseModel):
    """分享仪表板请求模式"""
    share_type: str = Field(..., description="分享类型")
    permissions: List[str] = Field(..., description="权限列表")
    expiry_date: Optional[datetime] = Field(None, description="过期时间")
    password: Optional[str] = Field(None, description="访问密码")
    allowed_users: Optional[List[str]] = Field(None, description="允许的用户")
    
    @validator('share_type')
    def validate_share_type(cls, v):
        """验证分享类型"""
        valid_types = ['public', 'private', 'link', 'embed']
        if v not in valid_types:
            raise ValueError(f'Invalid share type. Must be one of: {valid_types}')
        return v


class DashboardShareResponse(BaseModel):
    """分享仪表板响应模式"""
    share_id: str = Field(..., description="分享ID")
    share_url: str = Field(..., description="分享链接")
    embed_code: Optional[str] = Field(None, description="嵌入代码")
    qr_code: Optional[str] = Field(None, description="二维码")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


class DashboardExportRequest(BaseModel):
    """导出仪表板请求模式"""
    format: str = Field(..., description="导出格式")
    include_data: bool = Field(False, description="是否包含数据")
    time_range: Optional[TimeRangeEnum] = Field(None, description="时间范围")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤器")
    
    @validator('format')
    def validate_format(cls, v):
        """验证导出格式"""
        valid_formats = ['json', 'pdf', 'png', 'csv', 'excel']
        if v not in valid_formats:
            raise ValueError(f'Invalid export format. Must be one of: {valid_formats}')
        return v


class DashboardImportRequest(BaseModel):
    """导入仪表板请求模式"""
    data: Dict[str, Any] = Field(..., description="仪表板数据")
    overwrite: bool = Field(False, description="是否覆盖")
    update_data_sources: bool = Field(True, description="是否更新数据源")
    validate_only: bool = Field(False, description="仅验证")


# 仪表板数据模式
class DashboardDataRequest(BaseModel):
    """仪表板数据请求模式"""
    time_range: Optional[TimeRangeEnum] = Field(None, description="时间范围")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="过滤器")
    variables: Optional[Dict[str, Any]] = Field(default_factory=dict, description="变量")
    refresh: bool = Field(False, description="是否强制刷新")


class WidgetDataRequest(BaseModel):
    """组件数据请求模式"""
    widget_id: int = Field(..., description="组件ID")
    time_range: Optional[TimeRangeEnum] = Field(None, description="时间范围")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="过滤器")
    variables: Optional[Dict[str, Any]] = Field(default_factory=dict, description="变量")
    limit: Optional[int] = Field(None, description="数据限制", ge=1, le=10000)
    refresh: bool = Field(False, description="是否强制刷新")


class DashboardDataResponse(BaseModel):
    """仪表板数据响应模式"""
    dashboard_id: int = Field(..., description="仪表板ID")
    widgets_data: Dict[int, Any] = Field(..., description="组件数据")
    metadata: Dict[str, Any] = Field(..., description="元数据")
    last_updated: datetime = Field(..., description="最后更新时间")
    cache_hit: bool = Field(..., description="是否缓存命中")
    execution_time: float = Field(..., description="执行时间(秒)")
    
    class Config:
        from_attributes = True


class WidgetDataResponse(BaseModel):
    """组件数据响应模式"""
    widget_id: int = Field(..., description="组件ID")
    data: Any = Field(..., description="组件数据")
    metadata: Dict[str, Any] = Field(..., description="元数据")
    last_updated: datetime = Field(..., description="最后更新时间")
    cache_hit: bool = Field(..., description="是否缓存命中")
    execution_time: float = Field(..., description="执行时间(秒)")
    error: Optional[str] = Field(None, description="错误信息")
    
    class Config:
        from_attributes = True