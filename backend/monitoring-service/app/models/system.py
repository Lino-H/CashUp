#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 系统数据库模型

定义系统相关的数据库模型
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import (
    Column, String, Text, Float, Integer, Boolean, DateTime,
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func

from .base import BaseModel, TimestampMixin, SoftDeleteMixin, MetadataMixin, StatusMixin


class SystemConfig(BaseModel, MetadataMixin):
    """系统配置模型"""
    
    __tablename__ = 'system_configs'
    
    # 配置键
    config_key = Column(
        String(255),
        nullable=False,
        unique=True,
        comment="配置键"
    )
    
    # 配置值
    config_value = Column(
        JSONB,
        nullable=True,
        comment="配置值"
    )
    
    # 配置类型
    config_type = Column(
        String(50),
        nullable=False,
        default='string',
        comment="配置类型：string, number, boolean, json, array"
    )
    
    # 配置分组
    config_group = Column(
        String(100),
        nullable=False,
        default='general',
        comment="配置分组"
    )
    
    # 配置级别
    config_level = Column(
        String(20),
        nullable=False,
        default='user',
        comment="配置级别：system, admin, user"
    )
    
    # 是否敏感
    is_sensitive = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否敏感配置"
    )
    
    # 是否加密
    is_encrypted = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否加密存储"
    )
    
    # 是否只读
    is_readonly = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否只读"
    )
    
    # 默认值
    default_value = Column(
        JSONB,
        nullable=True,
        comment="默认值"
    )
    
    # 验证规则
    validation_rules = Column(
        JSONB,
        nullable=True,
        comment="验证规则"
    )
    
    # 显示信息
    display_name = Column(
        String(255),
        nullable=True,
        comment="显示名称"
    )
    
    display_order = Column(
        Integer,
        nullable=False,
        default=0,
        comment="显示顺序"
    )
    
    # 帮助信息
    help_text = Column(
        Text,
        nullable=True,
        comment="帮助文本"
    )
    
    # 更新信息
    updated_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="更新者ID"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_system_configs_key', 'config_key'),
        Index('idx_system_configs_group', 'config_group'),
        Index('idx_system_configs_level', 'config_level'),
        Index('idx_system_configs_sensitive', 'is_sensitive'),
        Index('idx_system_configs_readonly', 'is_readonly'),
        CheckConstraint(
            "config_type IN ('string', 'number', 'boolean', 'json', 'array')",
            name='ck_system_configs_type'
        ),
        CheckConstraint(
            "config_level IN ('system', 'admin', 'user')",
            name='ck_system_configs_level'
        ),
    )
    
    def get_display_name(self) -> str:
        """获取显示名称"""
        return self.display_name or self.config_key
    
    def get_config_value(self) -> Any:
        """获取配置值"""
        if self.is_encrypted and self.config_value:
            # 这里应该实现解密逻辑
            # 简化实现，直接返回值
            return self.config_value
        return self.config_value
    
    def set_config_value(self, value: Any, encrypt: bool = None):
        """设置配置值"""
        if encrypt is None:
            encrypt = self.is_sensitive
        
        if encrypt:
            # 这里应该实现加密逻辑
            # 简化实现，直接存储值
            self.config_value = value
            self.is_encrypted = True
        else:
            self.config_value = value
            self.is_encrypted = False
    
    def get_default_value(self) -> Any:
        """获取默认值"""
        return self.default_value
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """获取验证规则"""
        return self.validation_rules or {}
    
    def set_validation_rules(self, rules: Dict[str, Any]):
        """设置验证规则"""
        self.validation_rules = rules
    
    def validate_value(self, value: Any) -> bool:
        """验证配置值"""
        rules = self.get_validation_rules()
        if not rules:
            return True
        
        # 简化的验证逻辑
        if 'required' in rules and rules['required'] and value is None:
            return False
        
        if 'min_length' in rules and isinstance(value, str):
            if len(value) < rules['min_length']:
                return False
        
        if 'max_length' in rules and isinstance(value, str):
            if len(value) > rules['max_length']:
                return False
        
        if 'min_value' in rules and isinstance(value, (int, float)):
            if value < rules['min_value']:
                return False
        
        if 'max_value' in rules and isinstance(value, (int, float)):
            if value > rules['max_value']:
                return False
        
        return True


class SystemLog(BaseModel):
    """系统日志模型"""
    
    __tablename__ = 'system_logs'
    
    # 日志级别
    level = Column(
        String(20),
        nullable=False,
        comment="日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    
    # 日志来源
    logger_name = Column(
        String(255),
        nullable=False,
        comment="日志器名称"
    )
    
    # 模块信息
    module = Column(
        String(255),
        nullable=True,
        comment="模块名称"
    )
    
    function = Column(
        String(255),
        nullable=True,
        comment="函数名称"
    )
    
    line_number = Column(
        Integer,
        nullable=True,
        comment="行号"
    )
    
    # 日志消息
    message = Column(
        Text,
        nullable=False,
        comment="日志消息"
    )
    
    # 异常信息
    exception_type = Column(
        String(255),
        nullable=True,
        comment="异常类型"
    )
    
    exception_message = Column(
        Text,
        nullable=True,
        comment="异常消息"
    )
    
    stack_trace = Column(
        Text,
        nullable=True,
        comment="堆栈跟踪"
    )
    
    # 上下文信息
    request_id = Column(
        String(255),
        nullable=True,
        comment="请求ID"
    )
    
    user_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="用户ID"
    )
    
    session_id = Column(
        String(255),
        nullable=True,
        comment="会话ID"
    )
    
    client_ip = Column(
        String(45),
        nullable=True,
        comment="客户端IP"
    )
    
    user_agent = Column(
        Text,
        nullable=True,
        comment="用户代理"
    )
    
    # 额外数据
    extra_data = Column(
        JSONB,
        nullable=True,
        comment="额外数据"
    )
    
    # 时间戳
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        comment="时间戳"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_system_logs_level', 'level'),
        Index('idx_system_logs_logger', 'logger_name'),
        Index('idx_system_logs_module', 'module'),
        Index('idx_system_logs_timestamp', 'timestamp'),
        Index('idx_system_logs_request_id', 'request_id'),
        Index('idx_system_logs_user_id', 'user_id'),
        Index('idx_system_logs_client_ip', 'client_ip'),
        Index('idx_system_logs_level_timestamp', 'level', 'timestamp'),
        CheckConstraint(
            "level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')",
            name='ck_system_logs_level'
        ),
    )
    
    def get_extra_data(self) -> Dict[str, Any]:
        """获取额外数据"""
        return self.extra_data or {}
    
    def set_extra_data(self, data: Dict[str, Any]):
        """设置额外数据"""
        self.extra_data = data
    
    def is_error(self) -> bool:
        """是否为错误日志"""
        return self.level in ('ERROR', 'CRITICAL')
    
    def is_warning(self) -> bool:
        """是否为警告日志"""
        return self.level == 'WARNING'
    
    def has_exception(self) -> bool:
        """是否包含异常信息"""
        return self.exception_type is not None


class SystemBackup(BaseModel, MetadataMixin, StatusMixin):
    """系统备份模型"""
    
    __tablename__ = 'system_backups'
    
    # 备份名称
    name = Column(
        String(255),
        nullable=False,
        comment="备份名称"
    )
    
    # 备份类型
    backup_type = Column(
        String(50),
        nullable=False,
        comment="备份类型：full, incremental, differential"
    )
    
    # 备份范围
    backup_scope = Column(
        String(50),
        nullable=False,
        comment="备份范围：database, files, config, all"
    )
    
    # 文件信息
    file_path = Column(
        String(500),
        nullable=True,
        comment="备份文件路径"
    )
    
    file_size = Column(
        Integer,
        nullable=True,
        comment="文件大小（字节）"
    )
    
    file_hash = Column(
        String(255),
        nullable=True,
        comment="文件哈希"
    )
    
    # 压缩信息
    is_compressed = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否压缩"
    )
    
    compression_type = Column(
        String(20),
        nullable=True,
        comment="压缩类型"
    )
    
    original_size = Column(
        Integer,
        nullable=True,
        comment="原始大小（字节）"
    )
    
    # 加密信息
    is_encrypted = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否加密"
    )
    
    encryption_algorithm = Column(
        String(50),
        nullable=True,
        comment="加密算法"
    )
    
    # 时间信息
    started_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="开始时间"
    )
    
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="完成时间"
    )
    
    # 过期信息
    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="过期时间"
    )
    
    # 备份配