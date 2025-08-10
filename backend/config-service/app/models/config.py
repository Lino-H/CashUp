#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 配置模型

定义配置相关的数据库模型
"""

import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    String, Integer, Text, DateTime, Boolean, Enum, JSON,
    ForeignKey, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from ..core.database import Base


class ConfigType(str, enum.Enum):
    """
    配置类型枚举
    """
    SYSTEM = "system"          # 系统配置
    USER = "user"              # 用户配置
    STRATEGY = "strategy"      # 策略配置
    EXCHANGE = "exchange"      # 交易所配置
    NOTIFICATION = "notification"  # 通知配置
    TRADING = "trading"        # 交易配置
    RISK = "risk"              # 风险配置
    CUSTOM = "custom"          # 自定义配置


class ConfigScope(str, enum.Enum):
    """
    配置作用域枚举
    """
    GLOBAL = "global"          # 全局配置
    USER = "user"              # 用户级配置
    STRATEGY = "strategy"      # 策略级配置
    SESSION = "session"        # 会话级配置


class ConfigStatus(str, enum.Enum):
    """
    配置状态枚举
    """
    ACTIVE = "active"          # 激活
    INACTIVE = "inactive"      # 未激活
    DEPRECATED = "deprecated"  # 已废弃
    DRAFT = "draft"            # 草稿


class ConfigFormat(str, enum.Enum):
    """
    配置格式枚举
    """
    JSON = "json"              # JSON格式
    YAML = "yaml"              # YAML格式
    TOML = "toml"              # TOML格式
    ENV = "env"                # 环境变量格式
    XML = "xml"                # XML格式


class Config(Base):
    """
    配置模型
    
    存储系统的各种配置信息
    """
    __tablename__ = "configs"
    
    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="配置ID"
    )
    
    # 配置基本信息
    key: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="配置键"
    )
    
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="配置名称"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="配置描述"
    )
    
    # 配置分类
    type: Mapped[ConfigType] = mapped_column(
        Enum(ConfigType),
        nullable=False,
        comment="配置类型"
    )
    
    scope: Mapped[ConfigScope] = mapped_column(
        Enum(ConfigScope),
        nullable=False,
        default=ConfigScope.GLOBAL,
        comment="配置作用域"
    )
    
    category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="配置分类"
    )
    
    # 配置值
    value: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="配置值"
    )
    
    default_value: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="默认值"
    )
    
    # 配置格式和验证
    format: Mapped[ConfigFormat] = mapped_column(
        Enum(ConfigFormat),
        nullable=False,
        default=ConfigFormat.JSON,
        comment="配置格式"
    )
    
    schema: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="配置模式"
    )
    
    validation_rules: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="验证规则"
    )
    
    # 配置状态
    status: Mapped[ConfigStatus] = mapped_column(
        Enum(ConfigStatus),
        nullable=False,
        default=ConfigStatus.ACTIVE,
        comment="配置状态"
    )
    
    is_encrypted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否加密"
    )
    
    is_readonly: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否只读"
    )
    
    is_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否必需"
    )
    
    # 版本信息
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="配置版本"
    )
    
    # 关联信息
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="用户ID（用户级配置）"
    )
    
    strategy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="策略ID（策略级配置）"
    )
    
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("configs.id"),
        nullable=True,
        comment="父配置ID"
    )
    
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("config_templates.id"),
        nullable=True,
        comment="模板ID"
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
    
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="过期时间"
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
    tags: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="标签"
    )
    
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="元数据"
    )
    
    # 关联关系
    children = relationship("Config", back_populates="parent", cascade="all, delete-orphan")
    parent = relationship("Config", back_populates="children", remote_side=[id])
    template = relationship("ConfigTemplate", back_populates="configs")
    versions = relationship("ConfigVersion", back_populates="config", cascade="all, delete-orphan")
    audit_logs = relationship("ConfigAuditLog", back_populates="config", cascade="all, delete-orphan")
    
    # 表约束
    __table_args__ = (
        # 唯一约束
        UniqueConstraint('key', 'scope', 'user_id', 'strategy_id', name='uq_config_key_scope'),
        
        # 检查约束
        CheckConstraint('version > 0', name='ck_config_version_positive'),
        
        # 索引
        Index('idx_config_key', 'key'),
        Index('idx_config_type', 'type'),
        Index('idx_config_scope', 'scope'),
        Index('idx_config_status', 'status'),
        Index('idx_config_user_id', 'user_id'),
        Index('idx_config_strategy_id', 'strategy_id'),
        Index('idx_config_parent_id', 'parent_id'),
        Index('idx_config_template_id', 'template_id'),
        Index('idx_config_created_at', 'created_at'),
        Index('idx_config_key_type', 'key', 'type'),
        Index('idx_config_scope_user', 'scope', 'user_id'),
    )
    
    def __repr__(self) -> str:
        return f"<Config(id={self.id}, key={self.key}, type={self.type}, scope={self.scope})>"
    
    @property
    def is_active(self) -> bool:
        """
        检查配置是否激活
        
        Returns:
            bool: 配置是否激活
        """
        return self.status == ConfigStatus.ACTIVE
    
    @property
    def is_expired(self) -> bool:
        """
        检查配置是否过期
        
        Returns:
            bool: 配置是否过期
        """
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def get_effective_value(self) -> Dict[str, Any]:
        """
        获取有效配置值
        
        如果配置过期或未激活，返回默认值
        
        Returns:
            Dict[str, Any]: 有效配置值
        """
        if self.is_active and not self.is_expired:
            return self.value
        return self.default_value or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        return {
            "id": str(self.id),
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "scope": self.scope.value,
            "category": self.category,
            "value": self.value,
            "default_value": self.default_value,
            "format": self.format.value,
            "status": self.status.value,
            "version": self.version,
            "is_encrypted": self.is_encrypted,
            "is_readonly": self.is_readonly,
            "is_required": self.is_required,
            "user_id": str(self.user_id) if self.user_id else None,
            "strategy_id": str(self.strategy_id) if self.strategy_id else None,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "template_id": str(self.template_id) if self.template_id else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "tags": self.tags,
            "metadata": self.metadata
        }


class ConfigTemplate(Base):
    """
    配置模板模型
    
    存储配置模板信息
    """
    __tablename__ = "config_templates"
    
    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="模板ID"
    )
    
    # 模板基本信息
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="模板名称"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="模板描述"
    )
    
    # 模板内容
    template: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="模板内容"
    )
    
    schema: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="模板模式"
    )
    
    # 模板分类
    type: Mapped[ConfigType] = mapped_column(
        Enum(ConfigType),
        nullable=False,
        comment="模板类型"
    )
    
    category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="模板分类"
    )
    
    # 模板状态
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否激活"
    )
    
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否默认模板"
    )
    
    # 版本信息
    version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="1.0.0",
        comment="模板版本"
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
    
    # 元数据
    tags: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="标签"
    )
    
    # 关联关系
    configs = relationship("Config", back_populates="template")
    
    # 表约束
    __table_args__ = (
        # 索引
        Index('idx_template_name', 'name'),
        Index('idx_template_type', 'type'),
        Index('idx_template_category', 'category'),
        Index('idx_template_active', 'is_active'),
        Index('idx_template_default', 'is_default'),
    )
    
    def __repr__(self) -> str:
        return f"<ConfigTemplate(id={self.id}, name={self.name}, type={self.type})>"


class ConfigVersion(Base):
    """
    配置版本模型
    
    存储配置的历史版本
    """
    __tablename__ = "config_versions"
    
    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="版本ID"
    )
    
    # 关联配置
    config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("configs.id", ondelete="CASCADE"),
        nullable=False,
        comment="配置ID"
    )
    
    # 版本信息
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="版本号"
    )
    
    # 版本内容
    value: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="版本值"
    )
    
    # 变更信息
    change_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="变更摘要"
    )
    
    change_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="变更详情"
    )
    
    # 时间信息
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间"
    )
    
    # 创建者信息
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="创建者ID"
    )
    
    # 关联关系
    config = relationship("Config", back_populates="versions")
    
    # 表约束
    __table_args__ = (
        # 唯一约束
        UniqueConstraint('config_id', 'version', name='uq_config_version'),
        
        # 索引
        Index('idx_version_config_id', 'config_id'),
        Index('idx_version_version', 'version'),
        Index('idx_version_created_at', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<ConfigVersion(id={self.id}, config_id={self.config_id}, version={self.version})>"


class ConfigAuditLog(Base):
    """
    配置审计日志模型
    
    记录配置的操作历史
    """
    __tablename__ = "config_audit_logs"
    
    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="日志ID"
    )
    
    # 关联配置
    config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("configs.id", ondelete="CASCADE"),
        nullable=False,
        comment="配置ID"
    )
    
    # 操作信息
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="操作类型"
    )
    
    old_value: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="旧值"
    )
    
    new_value: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="新值"
    )
    
    # 操作详情
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="操作详情"
    )
    
    # 时间信息
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间"
    )
    
    # 操作者信息
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="操作者ID"
    )
    
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        comment="IP地址"
    )
    
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="用户代理"
    )
    
    # 关联关系
    config = relationship("Config", back_populates="audit_logs")
    
    # 表约束
    __table_args__ = (
        # 索引
        Index('idx_audit_config_id', 'config_id'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_user_id', 'user_id'),
        Index('idx_audit_created_at', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<ConfigAuditLog(id={self.id}, config_id={self.config_id}, action={self.action})>"