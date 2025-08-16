#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 健康检查数据库模型

定义健康检查相关的数据库模型
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import (
    Column, String, Text, Float, Integer, Boolean, DateTime,
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func

from .base import BaseModel, TimestampMixin, SoftDeleteMixin, MetadataMixin, StatusMixin


class HealthCheck(BaseModel, SoftDeleteMixin, MetadataMixin, StatusMixin):
    """健康检查模型"""
    
    __tablename__ = 'health_checks'
    
    # 基本信息
    name = Column(
        String(255),
        nullable=False,
        unique=True,
        comment="健康检查名称"
    )
    
    display_name = Column(
        String(255),
        nullable=True,
        comment="显示名称"
    )
    
    # 检查类型
    check_type = Column(
        String(50),
        nullable=False,
        comment="检查类型：http, tcp, database, redis, custom"
    )
    
    # 目标信息
    target_url = Column(
        String(500),
        nullable=True,
        comment="目标URL"
    )
    
    target_host = Column(
        String(255),
        nullable=True,
        comment="目标主机"
    )
    
    target_port = Column(
        Integer,
        nullable=True,
        comment="目标端口"
    )
    
    # 检查配置
    check_config = Column(
        JSONB,
        nullable=True,
        comment="检查配置"
    )
    
    # 时间配置
    interval_seconds = Column(
        Integer,
        nullable=False,
        default=60,
        comment="检查间隔（秒）"
    )
    
    timeout_seconds = Column(
        Integer,
        nullable=False,
        default=30,
        comment="超时时间（秒）"
    )
    
    # 重试配置
    max_retries = Column(
        Integer,
        nullable=False,
        default=3,
        comment="最大重试次数"
    )
    
    retry_interval = Column(
        Integer,
        nullable=False,
        default=5,
        comment="重试间隔（秒）"
    )
    
    # 阈值配置
    warning_threshold = Column(
        Float,
        nullable=True,
        comment="警告阈值（响应时间毫秒）"
    )
    
    critical_threshold = Column(
        Float,
        nullable=True,
        comment="严重阈值（响应时间毫秒）"
    )
    
    # 期望结果
    expected_status_code = Column(
        Integer,
        nullable=True,
        comment="期望状态码"
    )
    
    expected_content = Column(
        Text,
        nullable=True,
        comment="期望内容"
    )
    
    expected_headers = Column(
        JSONB,
        nullable=True,
        comment="期望响应头"
    )
    
    # 认证配置
    auth_config = Column(
        JSONB,
        nullable=True,
        comment="认证配置"
    )
    
    # 统计信息
    last_check_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后检查时间"
    )
    
    last_success_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后成功时间"
    )
    
    last_failure_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后失败时间"
    )
    
    total_checks = Column(
        Integer,
        default=0,
        nullable=False,
        comment="总检查次数"
    )
    
    success_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="成功次数"
    )
    
    failure_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="失败次数"
    )
    
    consecutive_failures = Column(
        Integer,
        default=0,
        nullable=False,
        comment="连续失败次数"
    )
    
    # 当前状态
    current_status = Column(
        String(20),
        nullable=False,
        default='unknown',
        comment="当前状态：healthy, warning, critical, unknown"
    )
    
    current_response_time = Column(
        Float,
        nullable=True,
        comment="当前响应时间（毫秒）"
    )
    
    current_error_message = Column(
        Text,
        nullable=True,
        comment="当前错误消息"
    )
    
    # 关系
    history = relationship(
        "HealthCheckHistory",
        back_populates="health_check",
        cascade="all, delete-orphan"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_health_checks_name', 'name'),
        Index('idx_health_checks_type', 'check_type'),
        Index('idx_health_checks_status', 'status'),
        Index('idx_health_checks_current_status', 'current_status'),
        Index('idx_health_checks_last_check', 'last_check_at'),
        Index('idx_health_checks_deleted', 'is_deleted'),
        CheckConstraint(
            "check_type IN ('http', 'tcp', 'database', 'redis', 'custom')",
            name='ck_health_checks_type'
        ),
        CheckConstraint(
            "current_status IN ('healthy', 'warning', 'critical', 'unknown')",
            name='ck_health_checks_current_status'
        ),
        CheckConstraint(
            "interval_seconds > 0",
            name='ck_health_checks_interval'
        ),
        CheckConstraint(
            "timeout_seconds > 0",
            name='ck_health_checks_timeout'
        ),
        CheckConstraint(
            "max_retries >= 0",
            name='ck_health_checks_retries'
        ),
    )
    
    def get_display_name(self) -> str:
        """获取显示名称"""
        return self.display_name or self.name
    
    def get_check_config(self) -> Dict[str, Any]:
        """获取检查配置"""
        return self.check_config or {}
    
    def set_check_config(self, config: Dict[str, Any]):
        """设置检查配置"""
        self.check_config = config
    
    def get_expected_headers(self) -> Dict[str, str]:
        """获取期望响应头"""
        return self.expected_headers or {}
    
    def set_expected_headers(self, headers: Dict[str, str]):
        """设置期望响应头"""
        self.expected_headers = headers
    
    def get_auth_config(self) -> Dict[str, Any]:
        """获取认证配置"""
        return self.auth_config or {}
    
    def set_auth_config(self, config: Dict[str, Any]):
        """设置认证配置"""
        self.auth_config = config
    
    def is_healthy(self) -> bool:
        """是否健康"""
        return self.current_status == 'healthy'
    
    def is_warning(self) -> bool:
        """是否警告"""
        return self.current_status == 'warning'
    
    def is_critical(self) -> bool:
        """是否严重"""
        return self.current_status == 'critical'
    
    def is_unknown(self) -> bool:
        """是否未知"""
        return self.current_status == 'unknown'
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.total_checks == 0:
            return 0.0
        return (self.success_count / self.total_checks) * 100
    
    def get_availability(self, hours: int = 24) -> float:
        """获取可用性（指定小时内）"""
        # 这里需要查询历史记录来计算
        # 简化实现，返回基于总体统计的可用性
        return self.get_success_rate()
    
    def should_check(self) -> bool:
        """是否应该执行检查"""
        if not self.is_active():
            return False
        
        if self.last_check_at is None:
            return True
        
        next_check = self.last_check_at + timedelta(seconds=self.interval_seconds)
        return datetime.utcnow() >= next_check
    
    def update_check_result(self, success: bool, response_time: Optional[float] = None, 
                          error_message: Optional[str] = None):
        """更新检查结果"""
        self.last_check_at = datetime.utcnow()
        self.total_checks += 1
        
        if success:
            self.success_count += 1
            self.consecutive_failures = 0
            self.last_success_at = datetime.utcnow()
            
            # 根据响应时间确定状态
            if response_time is not None:
                self.current_response_time = response_time
                if self.critical_threshold and response_time > self.critical_threshold:
                    self.current_status = 'critical'
                elif self.warning_threshold and response_time > self.warning_threshold:
                    self.current_status = 'warning'
                else:
                    self.current_status = 'healthy'
            else:
                self.current_status = 'healthy'
            
            self.current_error_message = None
        else:
            self.failure_count += 1
            self.consecutive_failures += 1
            self.last_failure_at = datetime.utcnow()
            self.current_status = 'critical'
            self.current_error_message = error_message
            self.current_response_time = None


class ServiceStatus(BaseModel, MetadataMixin):
    """服务状态模型"""
    
    __tablename__ = 'service_status'
    
    # 服务信息
    service_name = Column(
        String(255),
        nullable=False,
        unique=True,
        comment="服务名称"
    )
    
    service_type = Column(
        String(100),
        nullable=False,
        comment="服务类型"
    )
    
    # 状态信息
    status = Column(
        String(20),
        nullable=False,
        default='unknown',
        comment="状态：healthy, degraded, unhealthy, unknown"
    )
    
    health_score = Column(
        Float,
        nullable=True,
        comment="健康评分（0-100）"
    )
    
    # 版本信息
    version = Column(
        String(100),
        nullable=True,
        comment="服务版本"
    )
    
    build_info = Column(
        JSONB,
        nullable=True,
        comment="构建信息"
    )
    
    # 运行时信息
    uptime_seconds = Column(
        Integer,
        nullable=True,
        comment="运行时间（秒）"
    )
    
    start_time = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="启动时间"
    )
    
    # 资源使用
    cpu_usage = Column(
        Float,
        nullable=True,
        comment="CPU使用率"
    )
    
    memory_usage = Column(
        Float,
        nullable=True,
        comment="内存使用率"
    )
    
    disk_usage = Column(
        Float,
        nullable=True,
        comment="磁盘使用率"
    )
    
    # 连接信息
    active_connections = Column(
        Integer,
        nullable=True,
        comment="活跃连接数"
    )
    
    max_connections = Column(
        Integer,
        nullable=True,
        comment="最大连接数"
    )
    
    # 依赖服务
    dependencies = Column(
        JSONB,
        nullable=True,
        comment="依赖服务状态"
    )
    
    # 检查信息
    last_check_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后检查时间"
    )
    
    check_interval = Column(
        Integer,
        nullable=False,
        default=60,
        comment="检查间隔（秒）"
    )
    
    # 状态变更
    status_changed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="状态变更时间"
    )
    
    previous_status = Column(
        String(20),
        nullable=True,
        comment="之前状态"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_service_status_name', 'service_name'),
        Index('idx_service_status_type', 'service_type'),
        Index('idx_service_status_status', 'status'),
        Index('idx_service_status_last_check', 'last_check_at'),
        CheckConstraint(
            "status IN ('healthy', 'degraded', 'unhealthy', 'unknown')",
            name='ck_service_status_status'
        ),
        CheckConstraint(
            "health_score >= 0 AND health_score <= 100",
            name='ck_service_status_health_score'
        ),
    )
    
    def get_build_info(self) -> Dict[str, Any]:
        """获取构建信息"""
        return self.build_info or {}
    
    def set_build_info(self, info: Dict[str, Any]):
        """设置构建信息"""
        self.build_info = info
    
    def get_dependencies(self) -> Dict[str, str]:
        """获取依赖服务状态"""
        return self.dependencies or {}
    
    def set_dependencies(self, deps: Dict[str, str]):
        """设置依赖服务状态"""
        self.dependencies = deps
    
    def is_healthy(self) -> bool:
        """是否健康"""
        return self.status == 'healthy'
    
    def is_degraded(self) -> bool:
        """是否降级"""
        return self.status == 'degraded'
    
    def is_unhealthy(self) -> bool:
        """是否不健康"""
        return self.status == 'unhealthy'
    
    def is_unknown(self) -> bool:
        """是否未知"""
        return self.status == 'unknown'


class HealthCheckResult(BaseModel):
    """健康检查结果模型"""
    
    __tablename__ = 'health_check_results'
    
    # 关联健康检查
    health_check_id = Column(
        UUID(as_uuid=True),
        ForeignKey('health_checks.id', ondelete='CASCADE'),
        nullable=False,
        comment="健康检查ID"
    )
    
    # 检查结果
    success = Column(
        Boolean,
        nullable=False,
        comment="是否成功"
    )
    
    status = Column(
        String(20),
        nullable=False,
        comment="状态：healthy, warning, critical, unknown"
    )
    
    # 响应信息
    response_time = Column(
        Float,
        nullable=True,
        comment="响应时间（毫秒）"
    )
    
    status_code = Column(
        Integer,
        nullable=True,
        comment="状态码"
    )
    
    # 错误信息
    error_message = Column(
        Text,
        nullable=True,
        comment="错误消息"
    )
    
    # 详细信息
    details = Column(
        JSONB,
        nullable=True,
        comment="详细信息"
    )
    
    # 关系
    health_check = relationship("HealthCheck")
    
    # 索引
    __table_args__ = (
        Index('idx_health_check_results_check_id', 'health_check_id'),
        Index('idx_health_check_results_success', 'success'),
        Index('idx_health_check_results_status', 'status'),
        CheckConstraint(
            "status IN ('healthy', 'warning', 'critical', 'unknown')",
            name='ck_health_check_results_status'
        ),
    )
    
    def is_healthy(self) -> bool:
        """是否健康"""
        return self.status == 'healthy'
    
    def is_warning(self) -> bool:
        """是否警告"""
        return self.status == 'warning'
    
    def is_critical(self) -> bool:
        """是否严重"""
        return self.status == 'critical'
    
    def is_unknown(self) -> bool:
        """是否未知"""
        return self.status == 'unknown'
    
    def update_status(self, new_status: str, health_score: Optional[float] = None):
        """更新状态"""
        if self.status != new_status:
            self.previous_status = self.status
            self.status = new_status
            self.status_changed_at = datetime.utcnow()
        
        if health_score is not None:
            self.health_score = health_score
        
        self.last_check_at = datetime.utcnow()
    
    def get_uptime_duration(self) -> Optional[timedelta]:
        """获取运行时长"""
        if self.uptime_seconds is not None:
            return timedelta(seconds=self.uptime_seconds)
        elif self.start_time is not None:
            return datetime.utcnow() - self.start_time
        return None


class HealthCheckHistory(BaseModel):
    """健康检查历史模型"""
    
    __tablename__ = 'health_check_history'
    
    # 关联健康检查
    health_check_id = Column(
        UUID(as_uuid=True),
        ForeignKey('health_checks.id', ondelete='CASCADE'),
        nullable=False,
        comment="健康检查ID"
    )
    
    # 检查时间
    check_time = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        comment="检查时间"
    )
    
    # 检查结果
    success = Column(
        Boolean,
        nullable=False,
        comment="是否成功"
    )
    
    status = Column(
        String(20),
        nullable=False,
        comment="状态：healthy, warning, critical, unknown"
    )
    
    # 响应信息
    response_time = Column(
        Float,
        nullable=True,
        comment="响应时间（毫秒）"
    )
    
    status_code = Column(
        Integer,
        nullable=True,
        comment="状态码"
    )
    
    response_size = Column(
        Integer,
        nullable=True,
        comment="响应大小（字节）"
    )
    
    # 错误信息
    error_message = Column(
        Text,
        nullable=True,
        comment="错误消息"
    )
    
    error_type = Column(
        String(100),
        nullable=True,
        comment="错误类型"
    )
    
    # 详细信息
    details = Column(
        JSONB,
        nullable=True,
        comment="详细信息"
    )
    
    # 重试信息
    retry_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="重试次数"
    )
    
    # 关系
    health_check = relationship("HealthCheck", back_populates="history")
    
    # 索引
    __table_args__ = (
        Index('idx_health_check_history_check_id', 'health_check_id'),
        Index('idx_health_check_history_time', 'check_time'),
        Index('idx_health_check_history_success', 'success'),
        Index('idx_health_check_history_status', 'status'),
        Index('idx_health_check_history_check_time', 'health_check_id', 'check_time'),
        CheckConstraint(
            "status IN ('healthy', 'warning', 'critical', 'unknown')",
            name='ck_health_check_history_status'
        ),
    )
    
    def get_details(self) -> Dict[str, Any]:
        """获取详细信息"""
        return self.details or {}
    
    def set_details(self, details: Dict[str, Any]):
        """设置详细信息"""
        self.details = details
    
    def is_healthy(self) -> bool:
        """是否健康"""
        return self.status == 'healthy'
    
    def is_warning(self) -> bool:
        """是否警告"""
        return self.status == 'warning'
    
    def is_critical(self) -> bool:
        """是否严重"""
        return self.status == 'critical'
    
    def is_unknown(self) -> bool:
        """是否未知"""
        return self.status == 'unknown'