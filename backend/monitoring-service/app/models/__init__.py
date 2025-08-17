#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 数据库模型

导出所有数据库模型
"""

from .base import Base, TimestampMixin, SoftDeleteMixin
from .metrics import Metric, MetricValue, MetricTag
from .alerts import Alert, AlertRule, AlertHistory, NotificationChannel
from .health import HealthCheck, ServiceStatus, HealthCheckHistory
from .dashboard import Dashboard, DashboardComponent, DashboardTemplate
from .system import SystemConfig, SystemLog, SystemBackup
# from .user import User, UserSession, UserRole, Permission  # User module not implemented yet

__all__ = [
    # 基础模型
    'Base',
    'TimestampMixin',
    'SoftDeleteMixin',
    
    # 指标模型
    'Metric',
    'MetricValue',
    'MetricTag',
    
    # 告警模型
    'Alert',
    'AlertRule',
    'AlertHistory',
    'NotificationChannel',
    
    # 健康检查模型
    'HealthCheck',
    'ServiceStatus',
    'HealthCheckHistory',
    
    # 仪表板模型
    'Dashboard',
    'DashboardComponent',
    'DashboardTemplate',
    
    # 系统模型
    'SystemConfig',
    'SystemLog',
    'SystemBackup',
    
    # 用户模型 (not implemented yet)
    # 'User',
    # 'UserSession',
    # 'UserRole',
    # 'Permission',
]