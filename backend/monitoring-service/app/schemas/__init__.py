#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 监控服务数据模式

定义API请求和响应的数据模式
"""

from .metrics import (
    MetricCreate,
    MetricUpdate,
    MetricResponse,
    MetricListResponse,
    MetricValueCreate,
    MetricValueResponse,
    MetricValueListResponse,
    MetricValueBatchCreate,
    MetricAlertCreate,
    MetricAlertUpdate,
    MetricAlertResponse,
    MetricQueryRequest,
    MetricAggregateRequest,
    MetricAggregationResponse,
    MetricBatchRequest,
    MetricStatisticsResponse,
    MetricStatsResponse,
    MetricCollectionTrigger
)

from .alerts import (
    AlertCreate,
    AlertUpdate,
    AlertResponse,
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertRuleResponse,
    AlertChannelCreate,
    AlertChannelUpdate,
    AlertChannelResponse,
    AlertHistoryResponse,
    AlertSilenceRequest,
    AlertAcknowledgeRequest,
    AlertEscalateRequest,
    AlertBatchRequest,
    AlertStatisticsResponse
)

from .health import (
    HealthCheckCreate,
    HealthCheckUpdate,
    HealthCheckResponse,
    ServiceStatusResponse,
    HealthSummaryResponse,
    HealthHistoryResponse,
    HealthConfigResponse,
    HealthTestRequest,
    HealthBatchRequest
)

from .dashboard import (
    DashboardCreate,
    DashboardUpdate,
    DashboardResponse,
    DashboardWidgetCreate,
    DashboardWidgetUpdate,
    DashboardWidgetResponse,
    DashboardConfigCreate,
    DashboardConfigUpdate,
    DashboardConfigResponse,
    DashboardExportRequest,
    DashboardImportRequest,
    DashboardShareRequest,
    DashboardTemplateResponse
)

from .system import (
    SystemInfoResponse,
    SystemConfigResponse,
    SystemConfigUpdate,
    SystemStatusResponse,
    SystemResourcesResponse,
    SystemLogResponse,
    SystemBackupCreate,
    SystemBackupResponse,
    SystemMaintenanceTaskCreate,
    SystemMaintenanceTaskResponse,
    SystemPerformanceResponse,
    SystemSecurityResponse
)

__all__ = [
    # Metrics schemas
    "MetricCreate",
    "MetricUpdate",
    "MetricResponse",
    "MetricListResponse",
    "MetricValueCreate",
    "MetricValueResponse",
    "MetricValueListResponse",
    "MetricValueBatchCreate",
    "MetricAlertCreate",
    "MetricAlertUpdate",
    "MetricAlertResponse",
    "MetricQueryRequest",
    "MetricAggregateRequest",
    "MetricAggregationResponse",
    "MetricBatchRequest",
    "MetricStatisticsResponse",
    "MetricStatsResponse",
    "MetricCollectionTrigger",
    
    # Alerts schemas
    "AlertCreate",
    "AlertUpdate",
    "AlertResponse",
    "AlertRuleCreate",
    "AlertRuleUpdate",
    "AlertRuleResponse",
    "AlertChannelCreate",
    "AlertChannelUpdate",
    "AlertChannelResponse",
    "AlertHistoryResponse",
    "AlertSilenceRequest",
    "AlertAcknowledgeRequest",
    "AlertEscalateRequest",
    "AlertBatchRequest",
    "AlertStatisticsResponse",
    
    # Health schemas
    "HealthCheckCreate",
    "HealthCheckUpdate",
    "HealthCheckResponse",
    "ServiceStatusResponse",
    "HealthSummaryResponse",
    "HealthHistoryResponse",
    "HealthConfigResponse",
    "HealthTestRequest",
    "HealthBatchRequest",
    
    # Dashboard schemas
    "DashboardCreate",
    "DashboardUpdate",
    "DashboardResponse",
    "DashboardWidgetCreate",
    "DashboardWidgetUpdate",
    "DashboardWidgetResponse",
    "DashboardConfigCreate",
    "DashboardConfigUpdate",
    "DashboardConfigResponse",
    "DashboardExportRequest",
    "DashboardImportRequest",
    "DashboardShareRequest",
    "DashboardTemplateResponse",
    
    # System schemas
    "SystemInfoResponse",
    "SystemConfigResponse",
    "SystemConfigUpdate",
    "SystemStatusResponse",
    "SystemResourcesResponse",
    "SystemLogResponse",
    "SystemBackupCreate",
    "SystemBackupResponse",
    "SystemMaintenanceTaskCreate",
    "SystemMaintenanceTaskResponse",
    "SystemPerformanceResponse",
    "SystemSecurityResponse"
]