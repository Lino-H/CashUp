#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 仪表板API路由

仪表板相关的API端点
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Path, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
import json

from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.core.logging import get_logger, audit_log
from app.schemas.dashboard import (
    DashboardCreate, DashboardUpdate, DashboardResponse, DashboardListResponse,
    DashboardComponentCreate, DashboardComponentUpdate, DashboardComponentResponse,
    DashboardComponentListResponse, DashboardConfigCreate, DashboardConfigUpdate,
    DashboardConfigResponse, DashboardTemplateResponse, DashboardTemplateListResponse,
    DashboardFromTemplateRequest, DashboardCloneRequest, DashboardShareRequest,
    DashboardShareResponse, DashboardExportRequest, DashboardImportRequest,
    DashboardDataRequest, DashboardDataResponse, ComponentDataRequest,
    ComponentDataResponse
)
from app.schemas.common import PaginationParams, TimeRangeParams
from app.services.dashboard_service import DashboardService
from app.core.security import User

# 创建路由器
router = APIRouter()
logger = get_logger(__name__)

# 依赖注入
def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    """获取仪表板服务"""
    return DashboardService(db)


# ==================== 仪表板管理 ====================

@router.get("/", response_model=DashboardListResponse)
@require_permission("dashboard:read")
async def list_dashboards(
    pagination: PaginationParams = Depends(),
    dashboard_type: Optional[str] = Query(None, description="仪表板类型过滤"),
    tags: Optional[str] = Query(None, description="标签过滤（JSON格式）"),
    shared_only: bool = Query(False, description="仅显示共享的仪表板"),
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """获取仪表板列表"""
    try:
        # 解析标签过滤
        tags_filter = None
        if tags:
            tags_filter = json.loads(tags)
        
        result = await service.get_dashboards(
            skip=pagination.skip,
            limit=pagination.limit,
            dashboard_type=dashboard_type,
            tags=tags_filter,
            user_id=current_user.id,
            shared_only=shared_only
        )
        
        logger.info(
            f"Listed dashboards",
            extra={
                'user_id': current_user.id,
                'count': len(result['items']),
                'filters': {
                    'dashboard_type': dashboard_type,
                    'tags': tags_filter,
                    'shared_only': shared_only
                }
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list dashboards: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取仪表板列表失败")


@router.post("/", response_model=DashboardResponse, status_code=201)
@require_permission("dashboard:write")
@audit_log("create_dashboard", "dashboard")
async def create_dashboard(
    dashboard_data: DashboardCreate,
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """创建新仪表板"""
    try:
        # 设置创建者
        dashboard_data.created_by = current_user.id
        dashboard = await service.create_dashboard(dashboard_data)
        
        logger.info(
            f"Created dashboard: {dashboard.title}",
            extra={
                'user_id': current_user.id,
                'dashboard_id': dashboard.id,
                'dashboard_title': dashboard.title,
                'dashboard_type': dashboard.type
            }
        )
        
        return dashboard
        
    except ValueError as e:
        logger.warning(f"Invalid dashboard data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="创建仪表板失败")


@router.get("/{dashboard_id}", response_model=DashboardResponse)
@require_permission("dashboard:read")
async def get_dashboard(
    dashboard_id: int = Path(..., description="仪表板ID"),
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """获取仪表板详情"""
    try:
        dashboard = await service.get_dashboard(dashboard_id)
        if not dashboard:
            raise HTTPException(status_code=404, detail="仪表板不存在")
        
        # 检查访问权限
        if not dashboard.is_public and dashboard.created_by != current_user.id:
            # 检查是否有共享权限
            has_access = await service.check_dashboard_access(dashboard_id, current_user.id)
            if not has_access:
                raise HTTPException(status_code=403, detail="无权访问此仪表板")
        
        logger.debug(
            f"Retrieved dashboard: {dashboard.title}",
            extra={
                'user_id': current_user.id,
                'dashboard_id': dashboard_id
            }
        )
        
        return dashboard
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard {dashboard_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取仪表板详情失败")


@router.put("/{dashboard_id}", response_model=DashboardResponse)
@require_permission("dashboard:write")
@audit_log("update_dashboard", "dashboard")
async def update_dashboard(
    dashboard_id: int = Path(..., description="仪表板ID"),
    dashboard_data: DashboardUpdate = None,
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """更新仪表板"""
    try:
        # 检查权限
        dashboard = await service.get_dashboard(dashboard_id)
        if not dashboard:
            raise HTTPException(status_code=404, detail="仪表板不存在")
        
        if dashboard.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="无权修改此仪表板")
        
        updated_dashboard = await service.update_dashboard(dashboard_id, dashboard_data)
        
        logger.info(
            f"Updated dashboard: {updated_dashboard.title}",
            extra={
                'user_id': current_user.id,
                'dashboard_id': dashboard_id,
                'dashboard_title': updated_dashboard.title
            }
        )
        
        return updated_dashboard
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid dashboard update data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update dashboard {dashboard_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="更新仪表板失败")


@router.delete("/{dashboard_id}", status_code=204)
@require_permission("dashboard:delete")
@audit_log("delete_dashboard", "dashboard")
async def delete_dashboard(
    dashboard_id: int = Path(..., description="仪表板ID"),
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """删除仪表板"""
    try:
        # 检查权限
        dashboard = await service.get_dashboard(dashboard_id)
        if not dashboard:
            raise HTTPException(status_code=404, detail="仪表板不存在")
        
        if dashboard.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="无权删除此仪表板")
        
        success = await service.delete_dashboard(dashboard_id)
        
        logger.info(
            f"Deleted dashboard",
            extra={
                'user_id': current_user.id,
                'dashboard_id': dashboard_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete dashboard {dashboard_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="删除仪表板失败")


# ==================== 仪表板组件管理 ====================

@router.get("/{dashboard_id}/components", response_model=DashboardComponentListResponse)
@require_permission("dashboard:read")
async def list_dashboard_components(
    dashboard_id: int = Path(..., description="仪表板ID"),
    pagination: PaginationParams = Depends(),
    component_type: Optional[str] = Query(None, description="组件类型过滤"),
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """获取仪表板组件列表"""
    try:
        # 检查仪表板访问权限
        dashboard = await service.get_dashboard(dashboard_id)
        if not dashboard:
            raise HTTPException(status_code=404, detail="仪表板不存在")
        
        if not dashboard.is_public and dashboard.created_by != current_user.id:
            has_access = await service.check_dashboard_access(dashboard_id, current_user.id)
            if not has_access:
                raise HTTPException(status_code=403, detail="无权访问此仪表板")
        
        result = await service.get_dashboard_components(
            dashboard_id=dashboard_id,
            skip=pagination.skip,
            limit=pagination.limit,
            component_type=component_type
        )
        
        logger.info(
            f"Listed dashboard components",
            extra={
                'user_id': current_user.id,
                'dashboard_id': dashboard_id,
                'count': len(result['items']),
                'component_type': component_type
            }
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list dashboard components: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取仪表板组件列表失败")


@router.post("/{dashboard_id}/components", response_model=DashboardComponentResponse, status_code=201)
@require_permission("dashboard:write")
@audit_log("create_dashboard_component", "dashboard_component")
async def create_dashboard_component(
    dashboard_id: int = Path(..., description="仪表板ID"),
    component_data: DashboardComponentCreate = None,
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """创建仪表板组件"""
    try:
        # 检查权限
        dashboard = await service.get_dashboard(dashboard_id)
        if not dashboard:
            raise HTTPException(status_code=404, detail="仪表板不存在")
        
        if dashboard.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="无权修改此仪表板")
        
        # 设置仪表板ID
        component_data.dashboard_id = dashboard_id
        component = await service.create_dashboard_component(component_data)
        
        logger.info(
            f"Created dashboard component: {component.title}",
            extra={
                'user_id': current_user.id,
                'dashboard_id': dashboard_id,
                'component_id': component.id,
                'component_title': component.title,
                'component_type': component.type
            }
        )
        
        return component
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid component data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create dashboard component: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="创建仪表板组件失败")


@router.get("/components/{component_id}", response_model=DashboardComponentResponse)
@require_permission("dashboard:read")
async def get_dashboard_component(
    component_id: int = Path(..., description="组件ID"),
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """获取仪表板组件详情"""
    try:
        component = await service.get_dashboard_component(component_id)
        if not component:
            raise HTTPException(status_code=404, detail="组件不存在")
        
        # 检查仪表板访问权限
        dashboard = await service.get_dashboard(component.dashboard_id)
        if not dashboard.is_public and dashboard.created_by != current_user.id:
            has_access = await service.check_dashboard_access(component.dashboard_id, current_user.id)
            if not has_access:
                raise HTTPException(status_code=403, detail="无权访问此组件")
        
        logger.debug(
            f"Retrieved dashboard component: {component.title}",
            extra={
                'user_id': current_user.id,
                'component_id': component_id
            }
        )
        
        return component
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard component {component_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取组件详情失败")


@router.put("/components/{component_id}", response_model=DashboardComponentResponse)
@require_permission("dashboard:write")
@audit_log("update_dashboard_component", "dashboard_component")
async def update_dashboard_component(
    component_id: int = Path(..., description="组件ID"),
    component_data: DashboardComponentUpdate = None,
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """更新仪表板组件"""
    try:
        # 检查权限
        component = await service.get_dashboard_component(component_id)
        if not component:
            raise HTTPException(status_code=404, detail="组件不存在")
        
        dashboard = await service.get_dashboard(component.dashboard_id)
        if dashboard.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="无权修改此组件")
        
        updated_component = await service.update_dashboard_component(component_id, component_data)
        
        logger.info(
            f"Updated dashboard component: {updated_component.title}",
            extra={
                'user_id': current_user.id,
                'component_id': component_id,
                'component_title': updated_component.title
            }
        )
        
        return updated_component
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid component update data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update dashboard component {component_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="更新组件失败")


@router.delete("/components/{component_id}", status_code=204)
@require_permission("dashboard:delete")
@audit_log("delete_dashboard_component", "dashboard_component")
async def delete_dashboard_component(
    component_id: int = Path(..., description="组件ID"),
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """删除仪表板组件"""
    try:
        # 检查权限
        component = await service.get_dashboard_component(component_id)
        if not component:
            raise HTTPException(status_code=404, detail="组件不存在")
        
        dashboard = await service.get_dashboard(component.dashboard_id)
        if dashboard.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="无权删除此组件")
        
        success = await service.delete_dashboard_component(component_id)
        
        logger.info(
            f"Deleted dashboard component",
            extra={
                'user_id': current_user.id,
                'component_id': component_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete dashboard component {component_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="删除组件失败")


# ==================== 仪表板配置管理 ====================

@router.get("/{dashboard_id}/config", response_model=DashboardConfigResponse)
@require_permission("dashboard:read")
async def get_dashboard_config(
    dashboard_id: int = Path(..., description="仪表板ID"),
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """获取仪表板配置"""
    try:
        # 检查访问权限
        dashboard = await service.get_dashboard(dashboard_id)
        if not dashboard:
            raise HTTPException(status_code=404, detail="仪表板不存在")
        
        if not dashboard.is_public and dashboard.created_by != current_user.id:
            has_access = await service.check_dashboard_access(dashboard_id, current_user.id)
            if not has_access:
                raise HTTPException(status_code=403, detail="无权访问此仪表板")
        
        config = await service.get_dashboard_config(dashboard_id)
        
        logger.debug(
            f"Retrieved dashboard config",
            extra={
                'user_id': current_user.id,
                'dashboard_id': dashboard_id
            }
        )
        
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard config {dashboard_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取仪表板配置失败")


@router.post("/{dashboard_id}/config", response_model=DashboardConfigResponse, status_code=201)
@require_permission("dashboard:write")
@audit_log("create_dashboard_config", "dashboard_config")
async def create_dashboard_config(
    dashboard_id: int = Path(..., description="仪表板ID"),
    config_data: DashboardConfigCreate = None,
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """创建仪表板配置"""
    try:
        # 检查权限
        dashboard = await service.get_dashboard(dashboard_id)
        if not dashboard:
            raise HTTPException(status_code=404, detail="仪表板不存在")
        
        if dashboard.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="无权修改此仪表板")
        
        # 设置仪表板ID
        config_data.dashboard_id = dashboard_id
        config = await service.create_dashboard_config(config_data)
        
        logger.info(
            f"Created dashboard config",
            extra={
                'user_id': current_user.id,
                'dashboard_id': dashboard_id,
                'config_id': config.id
            }
        )
        
        return config
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid config data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create dashboard config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="创建仪表板配置失败")


@router.put("/{dashboard_id}/config", response_model=DashboardConfigResponse)
@require_permission("dashboard:write")
@audit_log("update_dashboard_config", "dashboard_config")
async def update_dashboard_config(
    dashboard_id: int = Path(..., description="仪表板ID"),
    config_data: DashboardConfigUpdate = None,
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """更新仪表板配置"""
    try:
        # 检查权限
        dashboard = await service.get_dashboard(dashboard_id)
        if not dashboard:
            raise HTTPException(status_code=404, detail="仪表板不存在")
        
        if dashboard.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="无权修改此仪表板")
        
        config = await service.update_dashboard_config(dashboard_id, config_data)
        
        logger.info(
            f"Updated dashboard config",
            extra={
                'user_id': current_user.id,
                'dashboard_id': dashboard_id
            }
        )
        
        return config
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid config update data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update dashboard config {dashboard_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="更新仪表板配置失败")


# ==================== 仪表板模板 ====================

@router.get("/templates", response_model=DashboardTemplateListResponse)
@require_permission("dashboard:read")
async def list_dashboard_templates(
    pagination: PaginationParams = Depends(),
    template_type: Optional[str] = Query(None, description="模板类型过滤"),
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """获取仪表板模板列表"""
    try:
        result = await service.get_dashboard_templates(
            skip=pagination.skip,
            limit=pagination.limit,
            template_type=template_type
        )
        
        logger.info(
            f"Listed dashboard templates",
            extra={
                'user_id': current_user.id,
                'count': len(result['items']),
                'template_type': template_type
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list dashboard templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取仪表板模板列表失败")


@router.get("/templates/{template_id}", response_model=DashboardTemplateResponse)
@require_permission("dashboard:read")
async def get_dashboard_template(
    template_id: int = Path(..., description="模板ID"),
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """获取仪表板模板详情"""
    try:
        template = await service.get_dashboard_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        logger.debug(
            f"Retrieved dashboard template: {template.name}",
            extra={
                'user_id': current_user.id,
                'template_id': template_id
            }
        )
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard template {template_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取模板详情失败")


@router.post("/from-template", response_model=DashboardResponse, status_code=201)
@require_permission("dashboard:write")
@audit_log("create_dashboard_from_template", "dashboard")
async def create_dashboard_from_template(
    template_data: DashboardFromTemplateRequest,
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """基于模板创建仪表板"""
    try:
        dashboard = await service.create_dashboard_from_template(
            template_data.template_id,
            template_data.title,
            template_data.description,
            current_user.id,
            template_data.customizations
        )
        
        logger.info(
            f"Created dashboard from template: {dashboard.title}",
            extra={
                'user_id': current_user.id,
                'dashboard_id': dashboard.id,
                'template_id': template_data.template_id,
                'dashboard_title': dashboard.title
            }
        )
        
        return dashboard
        
    except ValueError as e:
        logger.warning(f"Invalid template data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create dashboard from template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="基于模板创建仪表板失败")


# ==================== 仪表板操作 ====================

@router.post("/{dashboard_id}/clone", response_model=DashboardResponse, status_code=201)
@require_permission("dashboard:write")
@audit_log("clone_dashboard", "dashboard")
async def clone_dashboard(
    clone_data: DashboardCloneRequest,
    dashboard_id: int = Path(..., description="仪表板ID"),
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """克隆仪表板"""
    try:
        # 检查访问权限
        dashboard = await service.get_dashboard(dashboard_id)
        if not dashboard:
            raise HTTPException(status_code=404, detail="仪表板不存在")
        
        if not dashboard.is_public and dashboard.created_by != current_user.id:
            has_access = await service.check_dashboard_access(dashboard_id, current_user.id)
            if not has_access:
                raise HTTPException(status_code=403, detail="无权克隆此仪表板")
        
        cloned_dashboard = await service.clone_dashboard(
            dashboard_id,
            clone_data.title,
            current_user.id,
            clone_data.include_data
        )
        
        logger.info(
            f"Cloned dashboard: {cloned_dashboard.title}",
            extra={
                'user_id': current_user.id,
                'original_dashboard_id': dashboard_id,
                'cloned_dashboard_id': cloned_dashboard.id,
                'include_data': clone_data.include_data
            }
        )
        
        return cloned_dashboard
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clone dashboard {dashboard_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="克隆仪表板失败")


@router.post("/{dashboard_id}/share", response_model=DashboardShareResponse)
@require_permission("dashboard:share")
@audit_log("share_dashboard", "dashboard")
async def share_dashboard(
    share_data: DashboardShareRequest,
    dashboard_id: int = Path(..., description="仪表板ID"),
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """分享仪表板"""
    try:
        # 检查权限
        dashboard = await service.get_dashboard(dashboard_id)
        if not dashboard:
            raise HTTPException(status_code=404, detail="仪表板不存在")
        
        if dashboard.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="无权分享此仪表板")
        
        share_result = await service.share_dashboard(
            dashboard_id,
            share_data.share_type,
            share_data.permissions,
            share_data.expires_at,
            share_data.user_ids
        )
        
        logger.info(
            f"Shared dashboard",
            extra={
                'user_id': current_user.id,
                'dashboard_id': dashboard_id,
                'share_type': share_data.share_type,
                'user_count': len(share_data.user_ids) if share_data.user_ids else 0
            }
        )
        
        return share_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to share dashboard {dashboard_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="分享仪表板失败")


@router.post("/{dashboard_id}/export")
@require_permission("dashboard:export")
@audit_log("export_dashboard", "dashboard")
async def export_dashboard(
    export_data: DashboardExportRequest,
    dashboard_id: int = Path(..., description="仪表板ID"),
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """导出仪表板"""
    try:
        # 检查访问权限
        dashboard = await service.get_dashboard(dashboard_id)
        if not dashboard:
            raise HTTPException(status_code=404, detail="仪表板不存在")
        
        if not dashboard.is_public and dashboard.created_by != current_user.id:
            has_access = await service.check_dashboard_access(dashboard_id, current_user.id)
            if not has_access:
                raise HTTPException(status_code=403, detail="无权导出此仪表板")
        
        export_data_result = await service.export_dashboard(
            dashboard_id,
            export_data.format,
            export_data.include_data
        )
        
        logger.info(
            f"Exported dashboard",
            extra={
                'user_id': current_user.id,
                'dashboard_id': dashboard_id,
                'format': export_data.format,
                'include_data': export_data.include_data
            }
        )
        
        # 创建文件流响应
        filename = f"dashboard_{dashboard_id}.{export_data.format}"
        media_type = "application/json" if export_data.format == "json" else "application/octet-stream"
        
        return StreamingResponse(
            io.BytesIO(export_data_result.encode() if isinstance(export_data_result, str) else export_data_result),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export dashboard {dashboard_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="导出仪表板失败")


@router.post("/import", response_model=DashboardResponse, status_code=201)
@require_permission("dashboard:import")
@audit_log("import_dashboard", "dashboard")
async def import_dashboard(
    file: UploadFile = File(..., description="仪表板文件"),
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """导入仪表板"""
    try:
        # 读取文件内容
        content = await file.read()
        
        dashboard = await service.import_dashboard(
            content,
            file.filename,
            current_user.id
        )
        
        logger.info(
            f"Imported dashboard: {dashboard.title}",
            extra={
                'user_id': current_user.id,
                'dashboard_id': dashboard.id,
                'filename': file.filename
            }
        )
        
        return dashboard
        
    except ValueError as e:
        logger.warning(f"Invalid import file: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to import dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="导入仪表板失败")


# ==================== 仪表板数据 ====================

@router.post("/{dashboard_id}/data", response_model=DashboardDataResponse)
@require_permission("dashboard:read")
async def get_dashboard_data(
    data_request: DashboardDataRequest,
    dashboard_id: int = Path(..., description="仪表板ID"),
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """获取仪表板数据"""
    try:
        # 检查访问权限
        dashboard = await service.get_dashboard(dashboard_id)
        if not dashboard:
            raise HTTPException(status_code=404, detail="仪表板不存在")
        
        if not dashboard.is_public and dashboard.created_by != current_user.id:
            has_access = await service.check_dashboard_access(dashboard_id, current_user.id)
            if not has_access:
                raise HTTPException(status_code=403, detail="无权访问此仪表板")
        
        data = await service.get_dashboard_data(
            dashboard_id,
            data_request.time_range,
            data_request.filters,
            data_request.refresh
        )
        
        logger.debug(
            f"Retrieved dashboard data",
            extra={
                'user_id': current_user.id,
                'dashboard_id': dashboard_id,
                'refresh': data_request.refresh
            }
        )
        
        return data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard data {dashboard_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取仪表板数据失败")


@router.post("/components/{component_id}/data", response_model=ComponentDataResponse)
@require_permission("dashboard:read")
async def get_component_data(
    data_request: ComponentDataRequest,
    component_id: int = Path(..., description="组件ID"),
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """获取组件数据"""
    try:
        # 检查访问权限
        component = await service.get_dashboard_component(component_id)
        if not component:
            raise HTTPException(status_code=404, detail="组件不存在")
        
        dashboard = await service.get_dashboard(component.dashboard_id)
        if not dashboard.is_public and dashboard.created_by != current_user.id:
            has_access = await service.check_dashboard_access(component.dashboard_id, current_user.id)
            if not has_access:
                raise HTTPException(status_code=403, detail="无权访问此组件")
        
        data = await service.get_component_data(
            component_id,
            data_request.time_range,
            data_request.filters,
            data_request.refresh
        )
        
        logger.debug(
            f"Retrieved component data",
            extra={
                'user_id': current_user.id,
                'component_id': component_id,
                'refresh': data_request.refresh
            }
        )
        
        return data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get component data {component_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取组件数据失败")