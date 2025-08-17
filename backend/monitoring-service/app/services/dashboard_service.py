#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 仪表板服务

仪表板管理、组件配置和数据展示的业务逻辑
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc

from app.core.database import get_db
from app.core.cache import CacheManager
from app.core.exceptions import DashboardError, ServiceUnavailableError
from app.models.dashboard import Dashboard, DashboardComponent, DashboardConfig
from app.schemas.dashboard import (
    DashboardCreate, DashboardUpdate, DashboardWidgetCreate, DashboardWidgetUpdate,
    DashboardConfigCreate, DashboardConfigUpdate, DashboardTemplateCreateRequest,
    DashboardCloneRequest, DashboardShareRequest, DashboardExportRequest,
    DashboardImportRequest, DashboardDataRequest, WidgetDataRequest,
    DashboardTypeEnum, WidgetTypeEnum, RefreshIntervalEnum
)

logger = logging.getLogger(__name__)


class DashboardService:
    """仪表板服务类"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.data_cache = {}
        self.refresh_tasks = {}
        
    async def create_dashboard(self, db: Session, dashboard_data: DashboardCreate) -> Dashboard:
        """创建仪表板"""
        try:
            # 检查名称是否已存在
            existing = db.query(Dashboard).filter(Dashboard.name == dashboard_data.name).first()
            if existing:
                raise ValueError(f"Dashboard '{dashboard_data.name}' already exists")
            
            # 创建仪表板
            dashboard = Dashboard(
                name=dashboard_data.name,
                description=dashboard_data.description,
                dashboard_type=dashboard_data.dashboard_type,
                layout=dashboard_data.layout or {},
                config=dashboard_data.config or {},
                tags=dashboard_data.tags or [],
                is_public=dashboard_data.is_public,
                owner=dashboard_data.owner,
                refresh_interval=dashboard_data.refresh_interval,
                auto_refresh=dashboard_data.auto_refresh,
                theme=dashboard_data.theme,
                metadata=dashboard_data.metadata or {}
            )
            
            db.add(dashboard)
            db.commit()
            db.refresh(dashboard)
            
            # 如果有组件数据，创建组件
            if dashboard_data.widgets:
                for widget_data in dashboard_data.widgets:
                    widget = DashboardComponent(
                        dashboard_id=dashboard.id,
                        name=widget_data.name,
                        component_type=widget_data.widget_type,
                        position_x=widget_data.position.get('x', 0),
                        position_y=widget_data.position.get('y', 0),
                        width=widget_data.size.get('width', 6),
                        height=widget_data.size.get('height', 4),
                        query_config=widget_data.config or {},
                        data_source=widget_data.data_source,
                        refresh_interval=widget_data.refresh_interval
                    )
                    db.add(widget)
                
                db.commit()
            
            # 清除相关缓存
            await self.cache.clear_pattern("dashboards:*")
            
            logger.info(f"Created dashboard: {dashboard.name} (ID: {dashboard.id})")
            return dashboard
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create dashboard: {e}")
            raise DashboardError(f"Failed to create dashboard: {e}")
    
    async def get_dashboard(self, db: Session, dashboard_id: int) -> Optional[Dashboard]:
        """获取仪表板详情"""
        cache_key = f"dashboards:detail:{dashboard_id}"
        
        # 尝试从缓存获取
        cached_dashboard = await self.cache.get(cache_key)
        if cached_dashboard:
            return cached_dashboard
        
        # 从数据库获取
        dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
        
        if dashboard:
            # 获取关联的组件
            dashboard.components = db.query(DashboardComponent).filter(
                DashboardComponent.dashboard_id == dashboard_id
            ).all()
            
            # 缓存结果
            await self.cache.set(cache_key, dashboard, ttl=300)
        
        return dashboard
    
    async def get_dashboards(self, db: Session, 
                            dashboard_type: Optional[DashboardTypeEnum] = None,
                            owner: Optional[str] = None,
                            is_public: Optional[bool] = None,
                            tags: Optional[List[str]] = None,
                            limit: int = 100,
                            offset: int = 0) -> Tuple[List[Dashboard], int]:
        """获取仪表板列表"""
        try:
            # 构建查询
            query = db.query(Dashboard)
            
            # 应用过滤条件
            if dashboard_type:
                query = query.filter(Dashboard.dashboard_type == dashboard_type)
            
            if owner:
                query = query.filter(Dashboard.owner == owner)
            
            if is_public is not None:
                query = query.filter(Dashboard.is_public == is_public)
            
            if tags:
                for tag in tags:
                    query = query.filter(Dashboard.tags.op('@>')([tag]))
            
            # 获取总数
            total = query.count()
            
            # 应用排序和分页
            dashboards = query.order_by(desc(Dashboard.updated_at)).offset(offset).limit(limit).all()
            
            return dashboards, total
            
        except Exception as e:
            logger.error(f"Failed to get dashboards: {e}")
            raise DashboardError(f"Failed to get dashboards: {e}")
    
    async def update_dashboard(self, db: Session, dashboard_id: int, dashboard_data: DashboardUpdate) -> Optional[Dashboard]:
        """更新仪表板"""
        try:
            dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
            if not dashboard:
                return None
            
            # 更新字段
            update_data = dashboard_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(dashboard, field, value)
            
            dashboard.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(dashboard)
            
            # 清除相关缓存
            await self.cache.delete(f"dashboards:detail:{dashboard_id}")
            await self.cache.clear_pattern("dashboards:*")
            
            logger.info(f"Updated dashboard: {dashboard.name} (ID: {dashboard.id})")
            return dashboard
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update dashboard: {e}")
            raise DashboardError(f"Failed to update dashboard: {e}")
    
    async def delete_dashboard(self, db: Session, dashboard_id: int) -> bool:
        """删除仪表板"""
        try:
            dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
            if not dashboard:
                return False
            
            # 删除相关的组件
            db.query(DashboardComponent).filter(DashboardComponent.dashboard_id == dashboard_id).delete()
            
            # 删除相关的配置
            db.query(DashboardConfig).filter(DashboardConfig.dashboard_id == dashboard_id).delete()
            
            # 删除仪表板
            db.delete(dashboard)
            db.commit()
            
            # 停止相关的刷新任务
            if dashboard_id in self.refresh_tasks:
                self.refresh_tasks[dashboard_id].cancel()
                del self.refresh_tasks[dashboard_id]
            
            # 清除相关缓存
            await self.cache.delete(f"dashboards:detail:{dashboard_id}")
            await self.cache.clear_pattern("dashboards:*")
            
            logger.info(f"Deleted dashboard: {dashboard.name} (ID: {dashboard_id})")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete dashboard: {e}")
            raise DashboardError(f"Failed to delete dashboard: {e}")
    
    # 仪表板组件管理
    async def create_dashboard_widget(self, db: Session, widget_data: DashboardWidgetCreate) -> DashboardComponent:
        """创建仪表板组件"""
        try:
            # 检查仪表板是否存在
            dashboard = db.query(Dashboard).filter(Dashboard.id == widget_data.dashboard_id).first()
            if not dashboard:
                raise ValueError(f"Dashboard with ID {widget_data.dashboard_id} not found")
            
            # 创建组件
            widget = DashboardComponent(
                dashboard_id=widget_data.dashboard_id,
                name=widget_data.name,
                component_type=widget_data.widget_type,
                position_x=widget_data.position.get('x', 0),
                position_y=widget_data.position.get('y', 0),
                width=widget_data.size.get('width', 6),
                height=widget_data.size.get('height', 4),
                query_config=widget_data.config or {},
                data_source=widget_data.data_source,
                refresh_interval=widget_data.refresh_interval
            )
            
            db.add(widget)
            db.commit()
            db.refresh(widget)
            
            # 更新仪表板的更新时间
            dashboard.updated_at = datetime.utcnow()
            db.commit()
            
            # 清除相关缓存
            await self.cache.delete(f"dashboards:detail:{widget_data.dashboard_id}")
            await self.cache.clear_pattern("dashboards:*")
            
            logger.info(f"Created dashboard widget: {widget.name} (ID: {widget.id})")
            return widget
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create dashboard widget: {e}")
            raise DashboardError(f"Failed to create dashboard widget: {e}")
    
    async def get_dashboard_widget(self, db: Session, widget_id: int) -> Optional[DashboardComponent]:
        """获取仪表板组件详情"""
        cache_key = f"dashboards:widget:{widget_id}"
        
        # 尝试从缓存获取
        cached_widget = await self.cache.get(cache_key)
        if cached_widget:
            return cached_widget
        
        # 从数据库获取
        widget = db.query(DashboardComponent).filter(DashboardComponent.id == widget_id).first()
        
        if widget:
            # 缓存结果
            await self.cache.set(cache_key, widget, ttl=300)
        
        return widget
    
    async def get_dashboard_widgets(self, db: Session, dashboard_id: int) -> List[DashboardComponent]:
        """获取仪表板的所有组件"""
        cache_key = f"dashboards:widgets:{dashboard_id}"
        
        # 尝试从缓存获取
        cached_widgets = await self.cache.get(cache_key)
        if cached_widgets:
            return cached_widgets
        
        # 从数据库获取
        widgets = db.query(DashboardComponent).filter(
            DashboardComponent.dashboard_id == dashboard_id
        ).order_by(DashboardComponent.position).all()
        
        # 缓存结果
        await self.cache.set(cache_key, widgets, ttl=300)
        
        return widgets
    
    async def update_dashboard_widget(self, db: Session, widget_id: int, widget_data: DashboardWidgetUpdate) -> Optional[DashboardComponent]:
        """更新仪表板组件"""
        try:
            widget = db.query(DashboardComponent).filter(DashboardComponent.id == widget_id).first()
            if not widget:
                return None
            
            # 更新字段
            update_data = widget_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(widget, field, value)
            
            widget.updated_at = datetime.utcnow()
            
            # 更新仪表板的更新时间
            dashboard = db.query(Dashboard).filter(Dashboard.id == widget.dashboard_id).first()
            if dashboard:
                dashboard.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(widget)
            
            # 清除相关缓存
            await self.cache.delete(f"dashboards:widget:{widget_id}")
            await self.cache.delete(f"dashboards:widgets:{widget.dashboard_id}")
            await self.cache.delete(f"dashboards:detail:{widget.dashboard_id}")
            
            logger.info(f"Updated dashboard widget: {widget.name} (ID: {widget.id})")
            return widget
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update dashboard widget: {e}")
            raise DashboardError(f"Failed to update dashboard widget: {e}")
    
    async def delete_dashboard_widget(self, db: Session, widget_id: int) -> bool:
        """删除仪表板组件"""
        try:
            widget = db.query(DashboardComponent).filter(DashboardComponent.id == widget_id).first()
            if not widget:
                return False
            
            dashboard_id = widget.dashboard_id
            
            # 删除组件
            db.delete(widget)
            
            # 更新仪表板的更新时间
            dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
            if dashboard:
                dashboard.updated_at = datetime.utcnow()
            
            db.commit()
            
            # 清除相关缓存
            await self.cache.delete(f"dashboards:widget:{widget_id}")
            await self.cache.delete(f"dashboards:widgets:{dashboard_id}")
            await self.cache.delete(f"dashboards:detail:{dashboard_id}")
            
            logger.info(f"Deleted dashboard widget: {widget.name} (ID: {widget_id})")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete dashboard widget: {e}")
            raise DashboardError(f"Failed to delete dashboard widget: {e}")
    
    # 仪表板配置管理
    async def create_dashboard_config(self, db: Session, config_data: DashboardConfigCreate) -> DashboardConfig:
        """创建仪表板配置"""
        try:
            # 检查仪表板是否存在
            dashboard = db.query(Dashboard).filter(Dashboard.id == config_data.dashboard_id).first()
            if not dashboard:
                raise ValueError(f"Dashboard with ID {config_data.dashboard_id} not found")
            
            # 检查是否已存在配置
            existing = db.query(DashboardConfig).filter(
                and_(
                    DashboardConfig.dashboard_id == config_data.dashboard_id,
                    DashboardConfig.user_id == config_data.user_id
                )
            ).first()
            
            if existing:
                raise ValueError(f"Configuration already exists for user {config_data.user_id}")
            
            # 创建配置
            config = DashboardConfig(
                dashboard_id=config_data.dashboard_id,
                user_id=config_data.user_id,
                layout_config=config_data.layout_config or {},
                widget_config=config_data.widget_config or {},
                theme_config=config_data.theme_config or {},
                refresh_interval=config_data.refresh_interval,
                auto_refresh=config_data.auto_refresh,
                filters=config_data.filters or {},
                preferences=config_data.preferences or {}
            )
            
            db.add(config)
            db.commit()
            db.refresh(config)
            
            # 清除相关缓存
            await self.cache.clear_pattern("dashboards:*")
            
            logger.info(f"Created dashboard config for user {config.user_id} on dashboard {config.dashboard_id}")
            return config
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create dashboard config: {e}")
            raise DashboardError(f"Failed to create dashboard config: {e}")
    
    async def get_dashboard_config(self, db: Session, dashboard_id: int, user_id: str) -> Optional[DashboardConfig]:
        """获取仪表板配置"""
        cache_key = f"dashboards:config:{dashboard_id}:{user_id}"
        
        # 尝试从缓存获取
        cached_config = await self.cache.get(cache_key)
        if cached_config:
            return cached_config
        
        # 从数据库获取
        config = db.query(DashboardConfig).filter(
            and_(
                DashboardConfig.dashboard_id == dashboard_id,
                DashboardConfig.user_id == user_id
            )
        ).first()
        
        if config:
            # 缓存结果
            await self.cache.set(cache_key, config, ttl=300)
        
        return config
    
    async def update_dashboard_config(self, db: Session, dashboard_id: int, user_id: str, config_data: DashboardConfigUpdate) -> Optional[DashboardConfig]:
        """更新仪表板配置"""
        try:
            config = db.query(DashboardConfig).filter(
                and_(
                    DashboardConfig.dashboard_id == dashboard_id,
                    DashboardConfig.user_id == user_id
                )
            ).first()
            
            if not config:
                return None
            
            # 更新字段
            update_data = config_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(config, field, value)
            
            config.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(config)
            
            # 清除相关缓存
            await self.cache.delete(f"dashboards:config:{dashboard_id}:{user_id}")
            
            logger.info(f"Updated dashboard config for user {user_id} on dashboard {dashboard_id}")
            return config
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update dashboard config: {e}")
            raise DashboardError(f"Failed to update dashboard config: {e}")
    
    # 仪表板模板
    async def get_dashboard_templates(self, db: Session) -> List[Dict[str, Any]]:
        """获取仪表板模板"""
        try:
            cache_key = "dashboards:templates"
            
            # 尝试从缓存获取
            cached_templates = await self.cache.get(cache_key)
            if cached_templates:
                return cached_templates
            
            # 获取公共仪表板作为模板
            templates = db.query(Dashboard).filter(
                and_(
                    Dashboard.is_public == True,
                    Dashboard.dashboard_type.in_([DashboardType.TEMPLATE, DashboardType.SYSTEM])
                )
            ).all()
            
            template_list = []
            for template in templates:
                # 获取模板的组件
                widgets = db.query(DashboardComponent).filter(
            DashboardComponent.dashboard_id == template.id
                ).all()
                
                template_data = {
                    "id": template.id,
                    "name": template.name,
                    "description": template.description,
                    "dashboard_type": template.dashboard_type.value,
                    "layout": template.layout,
                    "config": template.config,
                    "tags": template.tags,
                    "theme": template.theme,
                    "widgets": [
                        {
                            "name": w.name,
                            "widget_type": w.widget_type.value,
                            "position": w.position,
                            "size": w.size,
                            "config": w.config,
                            "data_source": w.data_source,
                            "query": w.query,
                            "refresh_interval": w.refresh_interval.value if w.refresh_interval else None
                        }
                        for w in widgets
                    ],
                    "created_at": template.created_at.isoformat(),
                    "updated_at": template.updated_at.isoformat()
                }
                template_list.append(template_data)
            
            # 缓存结果
            await self.cache.set(cache_key, template_list, ttl=3600)
            
            return template_list
            
        except Exception as e:
            logger.error(f"Failed to get dashboard templates: {e}")
            raise DashboardError(f"Failed to get dashboard templates: {e}")
    
    async def create_dashboard_from_template(self, db: Session, request: DashboardTemplateCreateRequest) -> Dashboard:
        """基于模板创建仪表板"""
        try:
            # 获取模板
            template = db.query(Dashboard).filter(Dashboard.id == request.template_id).first()
            if not template:
                raise ValueError(f"Template with ID {request.template_id} not found")
            
            # 创建新仪表板
            dashboard = Dashboard(
                name=request.name,
                description=request.description or template.description,
                dashboard_type=DashboardType.CUSTOM,
                layout=template.layout.copy() if template.layout else {},
                config=template.config.copy() if template.config else {},
                tags=request.tags or template.tags,
                is_public=False,
                owner=request.owner,
                refresh_interval=template.refresh_interval,
                auto_refresh=template.auto_refresh,
                theme=template.theme,
                metadata={
                    "created_from_template": template.id,
                    "template_name": template.name
                }
            )
            
            db.add(dashboard)
            db.commit()
            db.refresh(dashboard)
            
            # 复制模板的组件
            template_widgets = db.query(DashboardComponent).filter(
            DashboardComponent.dashboard_id == template.id
            ).all()
            
            for template_widget in template_widgets:
                widget = DashboardComponent(
                    dashboard_id=dashboard.id,
                    name=template_widget.name,
                    widget_type=template_widget.widget_type,
                    position=template_widget.position.copy() if template_widget.position else {},
                    size=template_widget.size.copy() if template_widget.size else {},
                    config=template_widget.config.copy() if template_widget.config else {},
                    data_source=template_widget.data_source,
                    query=template_widget.query,
                    refresh_interval=template_widget.refresh_interval,
                    enabled=template_widget.enabled
                )
                db.add(widget)
            
            db.commit()
            
            # 清除相关缓存
            await self.cache.clear_pattern("dashboards:*")
            
            logger.info(f"Created dashboard from template: {dashboard.name} (ID: {dashboard.id})")
            return dashboard
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create dashboard from template: {e}")
            raise DashboardError(f"Failed to create dashboard from template: {e}")
    
    # 仪表板操作
    async def clone_dashboard(self, db: Session, dashboard_id: int, request: DashboardCloneRequest) -> Dashboard:
        """克隆仪表板"""
        try:
            # 获取原仪表板
            original = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
            if not original:
                raise ValueError(f"Dashboard with ID {dashboard_id} not found")
            
            # 创建克隆仪表板
            cloned = Dashboard(
                name=request.name,
                description=request.description or f"Clone of {original.description}",
                dashboard_type=DashboardType.CUSTOM,
                layout=original.layout.copy() if original.layout else {},
                config=original.config.copy() if original.config else {},
                tags=original.tags.copy() if original.tags else [],
                is_public=request.is_public,
                owner=request.owner,
                refresh_interval=original.refresh_interval,
                auto_refresh=original.auto_refresh,
                theme=original.theme,
                metadata={
                    "cloned_from": original.id,
                    "original_name": original.name,
                    "cloned_at": datetime.utcnow().isoformat()
                }
            )
            
            db.add(cloned)
            db.commit()
            db.refresh(cloned)
            
            # 克隆组件
            original_widgets = db.query(DashboardComponent).filter(
            DashboardComponent.dashboard_id == dashboard_id
            ).all()
            
            for original_widget in original_widgets:
                widget = DashboardComponent(
                    dashboard_id=cloned.id,
                    name=original_widget.name,
                    widget_type=original_widget.widget_type,
                    position=original_widget.position.copy() if original_widget.position else {},
                    size=original_widget.size.copy() if original_widget.size else {},
                    config=original_widget.config.copy() if original_widget.config else {},
                    data_source=original_widget.data_source,
                    query=original_widget.query,
                    refresh_interval=original_widget.refresh_interval,
                    enabled=original_widget.enabled
                )
                db.add(widget)
            
            db.commit()
            
            # 清除相关缓存
            await self.cache.clear_pattern("dashboards:*")
            
            logger.info(f"Cloned dashboard: {cloned.name} (ID: {cloned.id}) from {original.name}")
            return cloned
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to clone dashboard: {e}")
            raise DashboardError(f"Failed to clone dashboard: {e}")
    
    async def share_dashboard(self, db: Session, dashboard_id: int, request: DashboardShareRequest) -> Dict[str, Any]:
        """分享仪表板"""
        try:
            dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
            if not dashboard:
                raise ValueError(f"Dashboard with ID {dashboard_id} not found")
            
            # 生成分享链接
            share_token = str(uuid.uuid4())
            share_url = f"/shared/dashboard/{share_token}"
            
            # 更新仪表板元数据
            if not dashboard.metadata:
                dashboard.metadata = {}
            
            dashboard.metadata["share_info"] = {
                "token": share_token,
                "expires_at": (datetime.utcnow() + timedelta(days=request.expires_days)).isoformat() if request.expires_days else None,
                "permissions": request.permissions,
                "shared_by": request.shared_by,
                "shared_at": datetime.utcnow().isoformat()
            }
            
            dashboard.updated_at = datetime.utcnow()
            db.commit()
            
            # 清除相关缓存
            await self.cache.delete(f"dashboards:detail:{dashboard_id}")
            
            result = {
                "share_token": share_token,
                "share_url": share_url,
                "expires_at": dashboard.metadata["share_info"]["expires_at"],
                "permissions": request.permissions
            }
            
            logger.info(f"Shared dashboard: {dashboard.name} (ID: {dashboard_id})")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to share dashboard: {e}")
            raise DashboardError(f"Failed to share dashboard: {e}")
    
    async def export_dashboard(self, db: Session, dashboard_id: int, request: DashboardExportRequest) -> Dict[str, Any]:
        """导出仪表板"""
        try:
            dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
            if not dashboard:
                raise ValueError(f"Dashboard with ID {dashboard_id} not found")
            
            # 获取组件
            widgets = db.query(DashboardComponent).filter(
            DashboardComponent.dashboard_id == dashboard_id
            ).all()
            
            # 构建导出数据
            export_data = {
                "version": "1.0",
                "exported_at": datetime.utcnow().isoformat(),
                "exported_by": request.exported_by,
                "dashboard": {
                    "name": dashboard.name,
                    "description": dashboard.description,
                    "dashboard_type": dashboard.dashboard_type.value,
                    "layout": dashboard.layout,
                    "config": dashboard.config,
                    "tags": dashboard.tags,
                    "refresh_interval": dashboard.refresh_interval.value if dashboard.refresh_interval else None,
                    "auto_refresh": dashboard.auto_refresh,
                    "theme": dashboard.theme
                },
                "widgets": [
                    {
                        "name": w.name,
                        "widget_type": w.widget_type.value,
                        "position": w.position,
                        "size": w.size,
                        "config": w.config,
                        "data_source": w.data_source,
                        "query": w.query,
                        "refresh_interval": w.refresh_interval.value if w.refresh_interval else None,
                        "enabled": w.enabled
                    }
                    for w in widgets
                ]
            }
            
            # 根据格式返回数据
            if request.format == "json":
                return {
                    "format": "json",
                    "data": export_data,
                    "filename": f"{dashboard.name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
                }
            else:
                # 其他格式的导出逻辑
                return {
                    "format": request.format,
                    "data": json.dumps(export_data, indent=2),
                    "filename": f"{dashboard.name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{request.format}"
                }
            
        except Exception as e:
            logger.error(f"Failed to export dashboard: {e}")
            raise DashboardError(f"Failed to export dashboard: {e}")
    
    async def import_dashboard(self, db: Session, request: DashboardImportRequest) -> Dashboard:
        """导入仪表板"""
        try:
            # 解析导入数据
            if isinstance(request.data, str):
                import_data = json.loads(request.data)
            else:
                import_data = request.data
            
            # 验证数据格式
            if "dashboard" not in import_data or "widgets" not in import_data:
                raise ValueError("Invalid dashboard import data format")
            
            dashboard_data = import_data["dashboard"]
            widgets_data = import_data["widgets"]
            
            # 创建仪表板
            dashboard = Dashboard(
                name=request.name or dashboard_data["name"],
                description=dashboard_data.get("description"),
                dashboard_type=DashboardType.CUSTOM,
                layout=dashboard_data.get("layout", {}),
                config=dashboard_data.get("config", {}),
                tags=dashboard_data.get("tags", []),
                is_public=False,
                owner=request.owner,
                refresh_interval=RefreshInterval(dashboard_data["refresh_interval"]) if dashboard_data.get("refresh_interval") else None,
                auto_refresh=dashboard_data.get("auto_refresh", False),
                theme=dashboard_data.get("theme"),
                metadata={
                    "imported_at": datetime.utcnow().isoformat(),
                    "imported_by": request.owner,
                    "original_version": import_data.get("version")
                }
            )
            
            db.add(dashboard)
            db.commit()
            db.refresh(dashboard)
            
            # 创建组件
            for widget_data in widgets_data:
                widget = DashboardComponent(
                    dashboard_id=dashboard.id,
                    name=widget_data["name"],
                    widget_type=WidgetType(widget_data["widget_type"]),
                    position=widget_data.get("position", {}),
                    size=widget_data.get("size", {}),
                    config=widget_data.get("config", {}),
                    data_source=widget_data.get("data_source"),
                    query=widget_data.get("query"),
                    refresh_interval=RefreshInterval(widget_data["refresh_interval"]) if widget_data.get("refresh_interval") else None,
                    enabled=widget_data.get("enabled", True)
                )
                db.add(widget)
            
            db.commit()
            
            # 清除相关缓存
            await self.cache.clear_pattern("dashboards:*")
            
            logger.info(f"Imported dashboard: {dashboard.name} (ID: {dashboard.id})")
            return dashboard
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to import dashboard: {e}")
            raise DashboardError(f"Failed to import dashboard: {e}")
    
    # 数据获取
    async def get_dashboard_data(self, db: Session, dashboard_id: int, request: DashboardDataRequest) -> Dict[str, Any]:
        """获取仪表板数据"""
        try:
            dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
            if not dashboard:
                raise ValueError(f"Dashboard with ID {dashboard_id} not found")
            
            # 获取组件
            widgets = db.query(DashboardComponent).filter(
                and_(
                    DashboardComponent.dashboard_id == dashboard_id,
                    DashboardComponent.enabled == True
                )
            ).all()
            
            # 获取每个组件的数据
            widget_data = {}
            for widget in widgets:
                try:
                    data = await self._get_widget_data(widget, request.time_range, request.filters)
                    widget_data[widget.id] = data
                except Exception as e:
                    logger.error(f"Failed to get data for widget {widget.id}: {e}")
                    widget_data[widget.id] = {"error": str(e)}
            
            result = {
                "dashboard_id": dashboard_id,
                "timestamp": datetime.utcnow().isoformat(),
                "time_range": request.time_range,
                "filters": request.filters,
                "widgets": widget_data
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            raise DashboardError(f"Failed to get dashboard data: {e}")
    
    async def get_widget_data(self, db: Session, widget_id: int, request: WidgetDataRequest) -> Dict[str, Any]:
        """获取组件数据"""
        try:
            widget = db.query(DashboardComponent).filter(DashboardComponent.id == widget_id).first()
            if not widget:
                raise ValueError(f"Widget with ID {widget_id} not found")
            
            data = await self._get_widget_data(widget, request.time_range, request.filters)
            
            result = {
                "widget_id": widget_id,
                "timestamp": datetime.utcnow().isoformat(),
                "time_range": request.time_range,
                "filters": request.filters,
                "data": data
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get widget data: {e}")
            raise DashboardError(f"Failed to get widget data: {e}")
    
    async def _get_widget_data(self, widget: DashboardComponent, time_range: Optional[Dict[str, Any]] = None, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """获取单个组件的数据"""
        try:
            # 根据组件类型和数据源获取数据
            # 这里应该实现具体的数据获取逻辑
            
            # 示例实现
            if widget.component_type == WidgetTypeEnum.CHART:
                return await self._get_chart_data(widget, time_range, filters)
            elif widget.component_type == WidgetTypeEnum.TABLE:
                return await self._get_table_data(widget, time_range, filters)
            elif widget.component_type == WidgetTypeEnum.METRIC:
                return await self._get_metric_data(widget, time_range, filters)
            elif widget.component_type == WidgetTypeEnum.GAUGE:
                return await self._get_gauge_data(widget, time_range, filters)
            else:
                return {"message": f"Data for widget type {widget.component_type} not implemented"}
            
        except Exception as e:
            logger.error(f"Failed to get widget data: {e}")
            return {"error": str(e)}
    
    async def _get_chart_data(self, widget: DashboardComponent, time_range: Optional[Dict[str, Any]], filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """获取图表数据"""
        # 示例实现
        return {
            "type": "chart",
            "data": {
                "labels": ["Jan", "Feb", "Mar", "Apr", "May"],
                "datasets": [{
                    "label": "Sample Data",
                    "data": [10, 20, 30, 40, 50]
                }]
            }
        }
    
    async def _get_table_data(self, widget: DashboardComponent, time_range: Optional[Dict[str, Any]], filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """获取表格数据"""
        # 示例实现
        return {
            "type": "table",
            "data": {
                "columns": ["Name", "Value", "Status"],
                "rows": [
                    ["Item 1", 100, "Active"],
                    ["Item 2", 200, "Inactive"]
                ]
            }
        }
    
    async def _get_metric_data(self, widget: DashboardComponent, time_range: Optional[Dict[str, Any]], filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """获取指标数据"""
        # 示例实现
        return {
            "type": "metric",
            "data": {
                "value": 42,
                "unit": "%",
                "trend": "up",
                "change": 5.2
            }
        }
    
    async def _get_gauge_data(self, widget: DashboardComponent, time_range: Optional[Dict[str, Any]], filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """获取仪表盘数据"""
        # 示例实现
        return {
            "type": "gauge",
            "data": {
                "value": 75,
                "min": 0,
                "max": 100,
                "thresholds": {
                    "warning": 70,
                    "critical": 90
                }
            }
        }