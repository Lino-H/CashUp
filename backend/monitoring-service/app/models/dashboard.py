#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 仪表板数据库模型

定义仪表板相关的数据库模型
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


class Dashboard(BaseModel, SoftDeleteMixin, MetadataMixin, StatusMixin):
    """仪表板模型"""
    
    __tablename__ = 'dashboards'
    
    # 基本信息
    name = Column(
        String(255),
        nullable=False,
        comment="仪表板名称"
    )
    
    title = Column(
        String(255),
        nullable=True,
        comment="仪表板标题"
    )
    
    slug = Column(
        String(255),
        nullable=False,
        unique=True,
        comment="URL别名"
    )
    
    # 分类和标签
    category = Column(
        String(100),
        nullable=True,
        comment="分类"
    )
    
    # 布局配置
    layout_config = Column(
        JSONB,
        nullable=True,
        comment="布局配置"
    )
    
    # 样式配置
    style_config = Column(
        JSONB,
        nullable=True,
        comment="样式配置"
    )
    
    # 刷新配置
    refresh_interval = Column(
        Integer,
        nullable=False,
        default=300,
        comment="刷新间隔（秒）"
    )
    
    auto_refresh = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否自动刷新"
    )
    
    # 时间范围
    default_time_range = Column(
        String(50),
        nullable=False,
        default='1h',
        comment="默认时间范围"
    )
    
    # 权限配置
    is_public = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否公开"
    )
    
    is_shared = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否共享"
    )
    
    share_token = Column(
        String(255),
        nullable=True,
        unique=True,
        comment="共享令牌"
    )
    
    # 创建者信息
    created_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="创建者ID"
    )
    
    # 模板信息
    template_id = Column(
        UUID(as_uuid=True),
        ForeignKey('dashboard_templates.id', ondelete='SET NULL'),
        nullable=True,
        comment="模板ID"
    )
    
    # 统计信息
    view_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="查看次数"
    )
    
    last_viewed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后查看时间"
    )
    
    # 版本信息
    version = Column(
        Integer,
        default=1,
        nullable=False,
        comment="版本号"
    )
    
    # 关系
    components = relationship(
        "DashboardComponent",
        back_populates="dashboard",
        cascade="all, delete-orphan",
        order_by="DashboardComponent.position_order"
    )
    
    template = relationship("DashboardTemplate")
    
    # 索引
    __table_args__ = (
        Index('idx_dashboards_name', 'name'),
        Index('idx_dashboards_slug', 'slug'),
        Index('idx_dashboards_category', 'category'),
        Index('idx_dashboards_status', 'status'),
        Index('idx_dashboards_created_by', 'created_by'),
        Index('idx_dashboards_template_id', 'template_id'),
        Index('idx_dashboards_public', 'is_public'),
        Index('idx_dashboards_shared', 'is_shared'),
        Index('idx_dashboards_deleted', 'is_deleted'),
        CheckConstraint(
            "refresh_interval > 0",
            name='ck_dashboards_refresh_interval'
        ),
    )
    
    def get_title(self) -> str:
        """获取标题"""
        return self.title or self.name
    
    def get_layout_config(self) -> Dict[str, Any]:
        """获取布局配置"""
        return self.layout_config or {}
    
    def set_layout_config(self, config: Dict[str, Any]):
        """设置布局配置"""
        self.layout_config = config
    
    def get_style_config(self) -> Dict[str, Any]:
        """获取样式配置"""
        return self.style_config or {}
    
    def set_style_config(self, config: Dict[str, Any]):
        """设置样式配置"""
        self.style_config = config
    
    def increment_view_count(self):
        """增加查看次数"""
        self.view_count += 1
        self.last_viewed_at = datetime.utcnow()
    
    def increment_version(self):
        """增加版本号"""
        self.version += 1
    
    def generate_share_token(self) -> str:
        """生成共享令牌"""
        import secrets
        self.share_token = secrets.token_urlsafe(32)
        self.is_shared = True
        return self.share_token
    
    def revoke_share_token(self):
        """撤销共享令牌"""
        self.share_token = None
        self.is_shared = False


class DashboardComponent(BaseModel, SoftDeleteMixin, MetadataMixin, StatusMixin):
    """仪表板组件模型"""
    
    __tablename__ = 'dashboard_components'
    
    # 关联仪表板
    dashboard_id = Column(
        UUID(as_uuid=True),
        ForeignKey('dashboards.id', ondelete='CASCADE'),
        nullable=False,
        comment="仪表板ID"
    )
    
    # 基本信息
    name = Column(
        String(255),
        nullable=False,
        comment="组件名称"
    )
    
    title = Column(
        String(255),
        nullable=True,
        comment="组件标题"
    )
    
    # 组件类型
    component_type = Column(
        String(50),
        nullable=False,
        comment="组件类型：chart, table, metric, text, image, iframe"
    )
    
    # 位置和大小
    position_x = Column(
        Integer,
        nullable=False,
        default=0,
        comment="X坐标"
    )
    
    position_y = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Y坐标"
    )
    
    width = Column(
        Integer,
        nullable=False,
        default=6,
        comment="宽度（网格单位）"
    )
    
    height = Column(
        Integer,
        nullable=False,
        default=4,
        comment="高度（网格单位）"
    )
    
    position_order = Column(
        Integer,
        nullable=False,
        default=0,
        comment="排序顺序"
    )
    
    # 数据配置
    data_source = Column(
        String(100),
        nullable=True,
        comment="数据源"
    )
    
    query_config = Column(
        JSONB,
        nullable=True,
        comment="查询配置"
    )
    
    # 显示配置
    display_config = Column(
        JSONB,
        nullable=True,
        comment="显示配置"
    )
    
    # 样式配置
    style_config = Column(
        JSONB,
        nullable=True,
        comment="样式配置"
    )
    
    # 交互配置
    interaction_config = Column(
        JSONB,
        nullable=True,
        comment="交互配置"
    )
    
    # 刷新配置
    refresh_interval = Column(
        Integer,
        nullable=True,
        comment="刷新间隔（秒）"
    )
    
    auto_refresh = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否自动刷新"
    )
    
    # 缓存配置
    cache_duration = Column(
        Integer,
        nullable=True,
        comment="缓存时长（秒）"
    )
    
    # 条件显示
    visibility_conditions = Column(
        JSONB,
        nullable=True,
        comment="可见性条件"
    )
    
    # 关系
    dashboard = relationship("Dashboard", back_populates="components")
    
    # 索引
    __table_args__ = (
        Index('idx_dashboard_components_dashboard_id', 'dashboard_id'),
        Index('idx_dashboard_components_type', 'component_type'),
        Index('idx_dashboard_components_position', 'position_order'),
        Index('idx_dashboard_components_status', 'status'),
        Index('idx_dashboard_components_deleted', 'is_deleted'),
        UniqueConstraint(
            'dashboard_id', 'name',
            name='uq_dashboard_components_dashboard_name'
        ),
        CheckConstraint(
            "component_type IN ('chart', 'table', 'metric', 'text', 'image', 'iframe')",
            name='ck_dashboard_components_type'
        ),
        CheckConstraint(
            "width > 0 AND height > 0",
            name='ck_dashboard_components_size'
        ),
    )
    
    def get_title(self) -> str:
        """获取标题"""
        return self.title or self.name
    
    def get_query_config(self) -> Dict[str, Any]:
        """获取查询配置"""
        return self.query_config or {}
    
    def set_query_config(self, config: Dict[str, Any]):
        """设置查询配置"""
        self.query_config = config
    
    def get_display_config(self) -> Dict[str, Any]:
        """获取显示配置"""
        return self.display_config or {}
    
    def set_display_config(self, config: Dict[str, Any]):
        """设置显示配置"""
        self.display_config = config
    
    def get_style_config(self) -> Dict[str, Any]:
        """获取样式配置"""
        return self.style_config or {}
    
    def set_style_config(self, config: Dict[str, Any]):
        """设置样式配置"""
        self.style_config = config
    
    def get_interaction_config(self) -> Dict[str, Any]:
        """获取交互配置"""
        return self.interaction_config or {}
    
    def set_interaction_config(self, config: Dict[str, Any]):
        """设置交互配置"""
        self.interaction_config = config
    
    def get_visibility_conditions(self) -> Dict[str, Any]:
        """获取可见性条件"""
        return self.visibility_conditions or {}
    
    def set_visibility_conditions(self, conditions: Dict[str, Any]):
        """设置可见性条件"""
        self.visibility_conditions = conditions
    
    def is_chart(self) -> bool:
        """是否为图表组件"""
        return self.component_type == 'chart'
    
    def is_table(self) -> bool:
        """是否为表格组件"""
        return self.component_type == 'table'
    
    def is_metric(self) -> bool:
        """是否为指标组件"""
        return self.component_type == 'metric'
    
    def is_text(self) -> bool:
        """是否为文本组件"""
        return self.component_type == 'text'
    
    def is_image(self) -> bool:
        """是否为图片组件"""
        return self.component_type == 'image'
    
    def is_iframe(self) -> bool:
        """是否为iframe组件"""
        return self.component_type == 'iframe'
    
    def get_effective_refresh_interval(self) -> int:
        """获取有效刷新间隔"""
        if self.refresh_interval is not None:
            return self.refresh_interval
        return self.dashboard.refresh_interval if self.dashboard else 300


class DashboardTemplate(BaseModel, SoftDeleteMixin, MetadataMixin, StatusMixin):
    """仪表板模板模型"""
    
    __tablename__ = 'dashboard_templates'
    
    # 基本信息
    name = Column(
        String(255),
        nullable=False,
        unique=True,
        comment="模板名称"
    )
    
    title = Column(
        String(255),
        nullable=True,
        comment="模板标题"
    )
    
    # 分类信息
    category = Column(
        String(100),
        nullable=True,
        comment="模板分类"
    )
    
    # 模板配置
    template_config = Column(
        JSONB,
        nullable=False,
        comment="模板配置"
    )
    
    # 预览信息
    preview_image = Column(
        String(500),
        nullable=True,
        comment="预览图片URL"
    )
    
    preview_config = Column(
        JSONB,
        nullable=True,
        comment="预览配置"
    )
    
    # 使用统计
    usage_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="使用次数"
    )
    
    # 版本信息
    version = Column(
        String(20),
        nullable=False,
        default='1.0.0',
        comment="模板版本"
    )
    
    # 创建者信息
    created_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="创建者ID"
    )
    
    # 是否为系统模板
    is_system = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否为系统模板"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_dashboard_templates_name', 'name'),
        Index('idx_dashboard_templates_category', 'category'),
        Index('idx_dashboard_templates_status', 'status'),
        Index('idx_dashboard_templates_system', 'is_system'),
        Index('idx_dashboard_templates_created_by', 'created_by'),
        Index('idx_dashboard_templates_deleted', 'is_deleted'),
    )
    
    def get_title(self) -> str:
        """获取标题"""
        return self.title or self.name
    
    def get_template_config(self) -> Dict[str, Any]:
        """获取模板配置"""
        return self.template_config or {}
    
    def set_template_config(self, config: Dict[str, Any]):
        """设置模板配置"""
        self.template_config = config
    
    def get_preview_config(self) -> Dict[str, Any]:
        """获取预览配置"""
        return self.preview_config or {}
    
    def set_preview_config(self, config: Dict[str, Any]):
        """设置预览配置"""
        self.preview_config = config
    
    def increment_usage(self):
        """增加使用次数"""
        self.usage_count += 1


class DashboardConfig(BaseModel, MetadataMixin):
    """仪表板配置模型"""
    
    __tablename__ = 'dashboard_configs'
    
    # 关联仪表板
    dashboard_id = Column(
        UUID(as_uuid=True),
        ForeignKey('dashboards.id', ondelete='CASCADE'),
        nullable=False,
        comment="仪表板ID"
    )
    
    # 配置键
    config_key = Column(
        String(255),
        nullable=False,
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
        default='custom',
        comment="配置类型：system, user, custom"
    )
    
    # 是否加密
    is_encrypted = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否加密"
    )
    
    # 关系
    dashboard = relationship("Dashboard")
    
    # 索引
    __table_args__ = (
        Index('idx_dashboard_configs_dashboard_id', 'dashboard_id'),
        Index('idx_dashboard_configs_key', 'config_key'),
        Index('idx_dashboard_configs_type', 'config_type'),
        UniqueConstraint(
            'dashboard_id', 'config_key',
            name='uq_dashboard_configs_dashboard_key'
        ),
        CheckConstraint(
            "config_type IN ('system', 'user', 'custom')",
            name='ck_dashboard_configs_type'
        ),
    )
    
    def get_config_value(self) -> Any:
        """获取配置值"""
        if self.is_encrypted and self.config_value:
            # 这里应该实现解密逻辑
            # 简化实现，直接返回值
            return self.config_value
        return self.config_value
    
    def set_config_value(self, value: Any, encrypt: bool = False):
        """设置配置值"""
        if encrypt:
            # 这里应该实现加密逻辑
            # 简化实现，直接存储值
            self.config_value = value
            self.is_encrypted = True
        else:
            self.config_value =