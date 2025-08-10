#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 健康检查数据模式

定义健康检查相关的API请求和响应数据模式
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class HealthStatusEnum(str, Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    MAINTENANCE = "maintenance"


class ServiceTypeEnum(str, Enum):
    """服务类型枚举"""
    DATABASE = "database"
    CACHE = "cache"
    MESSAGE_QUEUE = "message_queue"
    API = "api"
    WEB_SERVICE = "web_service"
    MICROSERVICE = "microservice"
    EXTERNAL_SERVICE = "external_service"
    STORAGE = "storage"
    NETWORK = "network"
    CUSTOM = "custom"


class CheckTypeEnum(str, Enum):
    """检查类型枚举"""
    HTTP = "http"
    TCP = "tcp"
    DATABASE = "database"
    REDIS = "redis"
    RABBITMQ = "rabbitmq"
    KAFKA = "kafka"
    ELASTICSEARCH = "elasticsearch"
    CUSTOM = "custom"
    SCRIPT = "script"
    PING = "ping"


# 健康检查基础模式
class HealthCheckBase(BaseModel):
    """健康检查基础模式"""
    name: str = Field(..., description="检查名称", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="检查描述", max_length=1000)
    service_type: ServiceTypeEnum = Field(..., description="服务类型")
    check_type: CheckTypeEnum = Field(..., description="检查类型")
    endpoint: str = Field(..., description="检查端点", max_length=500)
    timeout: int = Field(30, description="超时时间(秒)", ge=1, le=300)
    interval: int = Field(60, description="检查间隔(秒)", ge=10, le=3600)
    retries: int = Field(3, description="重试次数", ge=0, le=10)
    retry_interval: int = Field(5, description="重试间隔(秒)", ge=1, le=60)
    expected_status_code: Optional[int] = Field(None, description="期望状态码", ge=100, le=599)
    expected_response_time: Optional[float] = Field(None, description="期望响应时间(秒)", ge=0.1, le=60)
    headers: Optional[Dict[str, str]] = Field(default_factory=dict, description="请求头")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="检查参数")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签")


class HealthCheckCreate(HealthCheckBase):
    """创建健康检查请求模式"""
    enabled: bool = Field(True, description="是否启用")
    critical: bool = Field(False, description="是否关键")
    alert_on_failure: bool = Field(True, description="失败时是否告警")
    failure_threshold: int = Field(3, description="失败阈值", ge=1, le=10)
    success_threshold: int = Field(1, description="成功阈值", ge=1, le=10)
    notification_channels: Optional[List[int]] = Field(default_factory=list, description="通知渠道ID列表")


class HealthCheckUpdate(BaseModel):
    """更新健康检查请求模式"""
    name: Optional[str] = Field(None, description="检查名称", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="检查描述", max_length=1000)
    endpoint: Optional[str] = Field(None, description="检查端点", max_length=500)
    timeout: Optional[int] = Field(None, description="超时时间(秒)", ge=1, le=300)
    interval: Optional[int] = Field(None, description="检查间隔(秒)", ge=10, le=3600)
    retries: Optional[int] = Field(None, description="重试次数", ge=0, le=10)
    retry_interval: Optional[int] = Field(None, description="重试间隔(秒)", ge=1, le=60)
    expected_status_code: Optional[int] = Field(None, description="期望状态码", ge=100, le=599)
    expected_response_time: Optional[float] = Field(None, description="期望响应时间(秒)", ge=0.1, le=60)
    headers: Optional[Dict[str, str]] = Field(None, description="请求头")
    params: Optional[Dict[str, Any]] = Field(None, description="检查参数")
    tags: Optional[List[str]] = Field(None, description="标签")
    enabled: Optional[bool] = Field(None, description="是否启用")
    critical: Optional[bool] = Field(None, description="是否关键")
    alert_on_failure: Optional[bool] = Field(None, description="失败时是否告警")
    failure_threshold: Optional[int] = Field(None, description="失败阈值", ge=1, le=10)
    success_threshold: Optional[int] = Field(None, description="成功阈值", ge=1, le=10)
    notification_channels: Optional[List[int]] = Field(None, description="通知渠道ID列表")


class HealthCheckResponse(HealthCheckBase):
    """健康检查响应模式"""
    id: int = Field(..., description="检查ID")
    enabled: bool = Field(..., description="是否启用")
    critical: bool = Field(..., description="是否关键")
    alert_on_failure: bool = Field(..., description="失败时是否告警")
    failure_threshold: int = Field(..., description="失败阈值")
    success_threshold: int = Field(..., description="成功阈值")
    status: HealthStatusEnum = Field(..., description="当前状态")
    last_check_at: Optional[datetime] = Field(None, description="最后检查时间")
    last_success_at: Optional[datetime] = Field(None, description="最后成功时间")
    last_failure_at: Optional[datetime] = Field(None, description="最后失败时间")
    consecutive_failures: int = Field(0, description="连续失败次数")
    consecutive_successes: int = Field(0, description="连续成功次数")
    total_checks: int = Field(0, description="总检查次数")
    success_count: int = Field(0, description="成功次数")
    failure_count: int = Field(0, description="失败次数")
    avg_response_time: Optional[float] = Field(None, description="平均响应时间(秒)")
    uptime_percentage: float = Field(100.0, description="可用性百分比")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    notification_channels: List[int] = Field(default_factory=list, description="通知渠道ID列表")
    
    class Config:
        from_attributes = True


# 服务状态模式
class ServiceStatusBase(BaseModel):
    """服务状态基础模式"""
    service_name: str = Field(..., description="服务名称", min_length=1, max_length=255)
    service_type: ServiceTypeEnum = Field(..., description="服务类型")
    version: Optional[str] = Field(None, description="服务版本", max_length=50)
    environment: Optional[str] = Field(None, description="环境", max_length=50)
    description: Optional[str] = Field(None, description="服务描述", max_length=1000)
    dependencies: Optional[List[str]] = Field(default_factory=list, description="依赖服务")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")


class ServiceStatusCreate(ServiceStatusBase):
    """创建服务状态请求模式"""
    enabled: bool = Field(True, description="是否启用")
    critical: bool = Field(False, description="是否关键服务")
    health_check_ids: Optional[List[int]] = Field(default_factory=list, description="关联健康检查ID列表")


class ServiceStatusUpdate(BaseModel):
    """更新服务状态请求模式"""
    service_name: Optional[str] = Field(None, description="服务名称", min_length=1, max_length=255)
    version: Optional[str] = Field(None, description="服务版本", max_length=50)
    environment: Optional[str] = Field(None, description="环境", max_length=50)
    description: Optional[str] = Field(None, description="服务描述", max_length=1000)
    dependencies: Optional[List[str]] = Field(None, description="依赖服务")
    tags: Optional[List[str]] = Field(None, description="标签")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    enabled: Optional[bool] = Field(None, description="是否启用")
    critical: Optional[bool] = Field(None, description="是否关键服务")
    health_check_ids: Optional[List[int]] = Field(None, description="关联健康检查ID列表")


class ServiceStatusResponse(ServiceStatusBase):
    """服务状态响应模式"""
    id: int = Field(..., description="服务ID")
    enabled: bool = Field(..., description="是否启用")
    critical: bool = Field(..., description="是否关键服务")
    status: HealthStatusEnum = Field(..., description="当前状态")
    last_check_at: Optional[datetime] = Field(None, description="最后检查时间")
    last_status_change_at: Optional[datetime] = Field(None, description="最后状态变更时间")
    uptime_percentage: float = Field(100.0, description="可用性百分比")
    downtime_duration: int = Field(0, description="停机时长(秒)")
    incident_count: int = Field(0, description="事件数量")
    health_check_count: int = Field(0, description="健康检查数量")
    healthy_checks: int = Field(0, description="健康检查数量")
    unhealthy_checks: int = Field(0, description="不健康检查数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    health_check_ids: List[int] = Field(default_factory=list, description="关联健康检查ID列表")
    
    class Config:
        from_attributes = True


# 健康检查执行结果模式
class HealthCheckResult(BaseModel):
    """健康检查执行结果模式"""
    check_id: int = Field(..., description="检查ID")
    status: HealthStatusEnum = Field(..., description="检查状态")
    response_time: Optional[float] = Field(None, description="响应时间(秒)")
    status_code: Optional[int] = Field(None, description="状态码")
    message: Optional[str] = Field(None, description="检查消息")
    error: Optional[str] = Field(None, description="错误信息")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")
    checked_at: datetime = Field(..., description="检查时间")
    
    class Config:
        from_attributes = True


class HealthCheckExecuteRequest(BaseModel):
    """执行健康检查请求模式"""
    check_ids: Optional[List[int]] = Field(None, description="检查ID列表")
    force: bool = Field(False, description="是否强制执行")
    async_execution: bool = Field(False, description="是否异步执行")


class HealthCheckBatchExecuteRequest(BaseModel):
    """批量执行健康检查请求模式"""
    service_types: Optional[List[ServiceTypeEnum]] = Field(None, description="服务类型列表")
    check_types: Optional[List[CheckTypeEnum]] = Field(None, description="检查类型列表")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    critical_only: bool = Field(False, description="仅关键检查")
    enabled_only: bool = Field(True, description="仅启用的检查")
    force: bool = Field(False, description="是否强制执行")
    async_execution: bool = Field(True, description="是否异步执行")


# 系统健康状态模式
class SystemHealthResponse(BaseModel):
    """系统健康状态响应模式"""
    overall_status: HealthStatusEnum = Field(..., description="整体状态")
    total_services: int = Field(..., description="总服务数")
    healthy_services: int = Field(..., description="健康服务数")
    degraded_services: int = Field(..., description="降级服务数")
    unhealthy_services: int = Field(..., description="不健康服务数")
    unknown_services: int = Field(..., description="未知状态服务数")
    maintenance_services: int = Field(..., description="维护中服务数")
    total_checks: int = Field(..., description="总检查数")
    healthy_checks: int = Field(..., description="健康检查数")
    unhealthy_checks: int = Field(..., description="不健康检查数")
    critical_issues: int = Field(..., description="关键问题数")
    system_uptime: float = Field(..., description="系统可用性")
    last_updated: datetime = Field(..., description="最后更新时间")
    services: List[ServiceStatusResponse] = Field(..., description="服务状态列表")
    critical_alerts: List[Dict[str, Any]] = Field(..., description="关键告警")
    recent_incidents: List[Dict[str, Any]] = Field(..., description="最近事件")
    performance_metrics: Dict[str, Any] = Field(..., description="性能指标")
    
    class Config:
        from_attributes = True


# 健康检查历史模式
class HealthCheckHistoryResponse(BaseModel):
    """健康检查历史响应模式"""
    id: int = Field(..., description="历史ID")
    check_id: int = Field(..., description="检查ID")
    status: HealthStatusEnum = Field(..., description="检查状态")
    response_time: Optional[float] = Field(None, description="响应时间(秒)")
    status_code: Optional[int] = Field(None, description="状态码")
    message: Optional[str] = Field(None, description="检查消息")
    error: Optional[str] = Field(None, description="错误信息")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")
    checked_at: datetime = Field(..., description="检查时间")
    
    class Config:
        from_attributes = True


# 健康检查配置模式
class HealthCheckConfigResponse(BaseModel):
    """健康检查配置响应模式"""
    global_timeout: int = Field(..., description="全局超时时间(秒)")
    global_interval: int = Field(..., description="全局检查间隔(秒)")
    global_retries: int = Field(..., description="全局重试次数")
    max_concurrent_checks: int = Field(..., description="最大并发检查数")
    enable_notifications: bool = Field(..., description="是否启用通知")
    notification_cooldown: int = Field(..., description="通知冷却时间(秒)")
    auto_recovery_enabled: bool = Field(..., description="是否启用自动恢复")
    maintenance_mode: bool = Field(..., description="是否维护模式")
    log_level: str = Field(..., description="日志级别")
    retention_days: int = Field(..., description="数据保留天数")
    custom_settings: Dict[str, Any] = Field(..., description="自定义设置")
    
    class Config:
        from_attributes = True


class HealthCheckConfigUpdate(BaseModel):
    """更新健康检查配置请求模式"""
    global_timeout: Optional[int] = Field(None, description="全局超时时间(秒)", ge=1, le=300)
    global_interval: Optional[int] = Field(None, description="全局检查间隔(秒)", ge=10, le=3600)
    global_retries: Optional[int] = Field(None, description="全局重试次数", ge=0, le=10)
    max_concurrent_checks: Optional[int] = Field(None, description="最大并发检查数", ge=1, le=100)
    enable_notifications: Optional[bool] = Field(None, description="是否启用通知")
    notification_cooldown: Optional[int] = Field(None, description="通知冷却时间(秒)", ge=60, le=3600)
    auto_recovery_enabled: Optional[bool] = Field(None, description="是否启用自动恢复")
    maintenance_mode: Optional[bool] = Field(None, description="是否维护模式")
    log_level: Optional[str] = Field(None, description="日志级别")
    retention_days: Optional[int] = Field(None, description="数据保留天数", ge=1, le=365)
    custom_settings: Optional[Dict[str, Any]] = Field(None, description="自定义设置")


# 健康检查统计模式
class HealthCheckStatisticsResponse(BaseModel):
    """健康检查统计响应模式"""
    total_checks: int = Field(..., description="总检查数")
    enabled_checks: int = Field(..., description="启用检查数")
    critical_checks: int = Field(..., description="关键检查数")
    healthy_checks: int = Field(..., description="健康检查数")
    degraded_checks: int = Field(..., description="降级检查数")
    unhealthy_checks: int = Field(..., description="不健康检查数")
    unknown_checks: int = Field(..., description="未知状态检查数")
    avg_response_time: float = Field(..., description="平均响应时间(秒)")
    avg_uptime: float = Field(..., description="平均可用性")
    total_executions: int = Field(..., description="总执行次数")
    successful_executions: int = Field(..., description="成功执行次数")
    failed_executions: int = Field(..., description="失败执行次数")
    service_type_distribution: Dict[str, int] = Field(..., description="服务类型分布")
    check_type_distribution: Dict[str, int] = Field(..., description="检查类型分布")
    status_distribution: Dict[str, int] = Field(..., description="状态分布")
    response_time_distribution: Dict[str, int] = Field(..., description="响应时间分布")
    uptime_distribution: Dict[str, int] = Field(..., description="可用性分布")
    top_failing_checks: List[Dict[str, Any]] = Field(..., description="失败最多的检查")
    top_slow_checks: List[Dict[str, Any]] = Field(..., description="最慢的检查")
    recent_incidents: List[Dict[str, Any]] = Field(..., description="最近事件")
    
    class Config:
        from_attributes = True


class HealthCheckTrendResponse(BaseModel):
    """健康检查趋势响应模式"""
    time_series: List[Dict[str, Any]] = Field(..., description="时间序列数据")
    uptime_trend: List[Dict[str, Any]] = Field(..., description="可用性趋势")
    response_time_trend: List[Dict[str, Any]] = Field(..., description="响应时间趋势")
    failure_rate_trend: List[Dict[str, Any]] = Field(..., description="失败率趋势")
    incident_trend: List[Dict[str, Any]] = Field(..., description="事件趋势")
    seasonal_patterns: Dict[str, Any] = Field(..., description="季节性模式")
    anomalies: List[Dict[str, Any]] = Field(..., description="异常点")
    predictions: Dict[str, Any] = Field(..., description="预测数据")
    
    class Config:
        from_attributes = True