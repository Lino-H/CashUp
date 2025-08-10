#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 仪表板API端点

提供监控仪表板管理和可视化配置的API接口
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session

from ....core.database import get_db
from ....schemas.dashboard import (
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
from ....services.dashboard import DashboardService
from ....core.exceptions import (
    ConfigurationError,
    ServiceUnavailableError
)

logger = logging.getLogger(__name__)

router = APIRouter()


# 仪表板管理
@router.get("/", response_model=List[DashboardResponse])
async def list_dashboards(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    dashboard_type: Optional[str] = Query(None, description="仪表板类型"),
    is_public: Optional[bool] = Query(None, description="是否公开"),
    created_by: Optional[str] = Query(None, description="创建者"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """
    获取仪表板列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的记录数
        dashboard_type: 仪表板类型过滤
        is_public: 是否公开过滤
        created_by: 创建者过滤
        search: 搜索关键词
        db: 数据库会话
        
    Returns:
        List[DashboardResponse]: 仪表板列表
    """
    try:
        dashboard_service = DashboardService(db)
        dashboards = await dashboard_service.list_dashboards(
            skip=skip,
            limit=limit,
            dashboard_type=dashboard_type,
            is_public=is_public,
            created_by=created_by,
            search=search
        )
        return dashboards
    except Exception as e:
        logger.error(f"Failed to list dashboards: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboards")


@router.post("/", response_model=DashboardResponse)
async def create_dashboard(
    dashboard: DashboardCreate,
    db: Session = Depends(get_db)
):
    """
    创建新仪表板
    
    Args:
        dashboard: 仪表板创建数据
        db: 数据库会话
        
    Returns:
        DashboardResponse: 创建的仪表板
    """
    try:
        dashboard_service = DashboardService(db)
        created_dashboard = await dashboard_service.create_dashboard(dashboard)
        return created_dashboard
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to create dashboard")


@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: int = Path(..., description="仪表板ID"),
    include_widgets: bool = Query(True, description="是否包含组件"),
    db: Session = Depends(get_db)
):
    """
    获取指定仪表板详情
    
    Args:
        dashboard_id: 仪表板ID
        include_widgets: 是否包含组件
        db: 数据库会话
        
    Returns:
        DashboardResponse: 仪表板详情
    """
    try:
        dashboard_service = DashboardService(db)
        dashboard = await dashboard_service.get_dashboard(dashboard_id, include_widgets)
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        return dashboard
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard {dashboard_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard")


@router.put("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: int = Path(..., description="仪表板ID"),
    dashboard_update: DashboardUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """
    更新仪表板
    
    Args:
        dashboard_id: 仪表板ID
        dashboard_update: 仪表板更新数据
        db: 数据库会话
        
    Returns:
        DashboardResponse: 更新后的仪表板
    """
    try:
        dashboard_service = DashboardService(db)
        updated_dashboard = await dashboard_service.update_dashboard(dashboard_id, dashboard_update)
        if not updated_dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        return updated_dashboard
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update dashboard {dashboard_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update dashboard")


@router.delete("/{dashboard_id}")
async def delete_dashboard(
    dashboard_id: int = Path(..., description="仪表板ID"),
    db: Session = Depends(get_db)
):
    """
    删除仪表板
    
    Args:
        dashboard_id: 仪表板ID
        db: 数据库会话
        
    Returns:
        dict: 删除结果
    """
    try:
        dashboard_service = DashboardService(db)
        success = await dashboard_service.delete_dashboard(dashboard_id)
        if not success:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        return {"message": "Dashboard deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete dashboard {dashboard_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete dashboard")


# 仪表板组件管理
@router.get("/{dashboard_id}/widgets", response_model=List[DashboardWidgetResponse])
async def list_dashboard_widgets(
    dashboard_id: int = Path(..., description="仪表板ID"),
    widget_type: Optional[str] = Query(None, description="组件类型"),
    db: Session = Depends(get_db)
):
    """
    获取仪表板组件列表
    
    Args:
        dashboard_id: 仪表板ID
        widget_type: 组件类型过滤
        db: 数据库会话
        
    Returns:
        List[DashboardWidgetResponse]: 组件列表
    """
    try:
        dashboard_service = DashboardService(db)
        widgets = await dashboard_service.list_dashboard_widgets(
            dashboard_id=dashboard_id,
            widget_type=widget_type
        )
        return widgets
    except Exception as e:
        logger.error(f"Failed to list dashboard widgets for dashboard {dashboard_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard widgets")


@router.post("/{dashboard_id}/widgets", response_model=DashboardWidgetResponse)
async def create_dashboard_widget(
    dashboard_id: int = Path(..., description="仪表板ID"),
    widget: DashboardWidgetCreate = Body(...),
    db: Session = Depends(get_db)
):
    """
    创建仪表板组件
    
    Args:
        dashboard_id: 仪表板ID
        widget: 组件创建数据
        db: 数据库会话
        
    Returns:
        DashboardWidgetResponse: 创建的组件
    """
    try:
        dashboard_service = DashboardService(db)
        created_widget = await dashboard_service.create_dashboard_widget(dashboard_id, widget)
        return created_widget
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create dashboard widget: {e}")
        raise HTTPException(status_code=500, detail="Failed to create dashboard widget")


@router.get("/{dashboard_id}/widgets/{widget_id}", response_model=DashboardWidgetResponse)
async def get_dashboard_widget(
    dashboard_id: int = Path(..., description="仪表板ID"),
    widget_id: int = Path(..., description="组件ID"),
    db: Session = Depends(get_db)
):
    """
    获取指定仪表板组件详情
    
    Args:
        dashboard_id: 仪表板ID
        widget_id: 组件ID
        db: 数据库会话
        
    Returns:
        DashboardWidgetResponse: 组件详情
    """
    try:
        dashboard_service = DashboardService(db)
        widget = await dashboard_service.get_dashboard_widget(dashboard_id, widget_id)
        if not widget:
            raise HTTPException(status_code=404, detail="Dashboard widget not found")
        return widget
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard widget {widget_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard widget")


@router.put("/{dashboard_id}/widgets/{widget_id}", response_model=DashboardWidgetResponse)
async def update_dashboard_widget(
    dashboard_id: int = Path(..., description="仪表板ID"),
    widget_id: int = Path(..., description="组件ID"),
    widget_update: DashboardWidgetUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """
    更新仪表板组件
    
    Args:
        dashboard_id: 仪表板ID
        widget_id: 组件ID
        widget_update: 组件更新数据
        db: 数据库会话
        
    Returns:
        DashboardWidgetResponse: 更新后的组件
    """
    try:
        dashboard_service = DashboardService(db)
        updated_widget = await dashboard_service.update_dashboard_widget(
            dashboard_id, widget_id, widget_update
        )
        if not updated_widget:
            raise HTTPException(status_code=404, detail="Dashboard widget not found")
        return updated_widget
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update dashboard widget {widget_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update dashboard widget")


@router.delete("/{dashboard_id}/widgets/{widget_id}")
async def delete_dashboard_widget(
    dashboard_id: int = Path(..., description="仪表板ID"),
    widget_id: int = Path(..., description="组件ID"),
    db: Session = Depends(get_db)
):
    """
    删除仪表板组件
    
    Args:
        dashboard_id: 仪表板ID
        widget_id: 组件ID
        db: 数据库会话
        
    Returns:
        dict: 删除结果
    """
    try:
        dashboard_service = DashboardService(db)
        success = await dashboard_service.delete_dashboard_widget(dashboard_id, widget_id)
        if not success:
            raise HTTPException(status_code=404, detail="Dashboard widget not found")
        return {"message": "Dashboard widget deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete dashboard widget {widget_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete dashboard widget")


# 仪表板配置管理
@router.get("/config", response_model=List[DashboardConfigResponse])
async def list_dashboard_configs(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    user_id: Optional[str] = Query(None, description="用户ID"),
    db: Session = Depends(get_db)
):
    """
    获取仪表板配置列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的记录数
        user_id: 用户ID过滤
        db: 数据库会话
        
    Returns:
        List[DashboardConfigResponse]: 配置列表
    """
    try:
        dashboard_service = DashboardService(db)
        configs = await dashboard_service.list_dashboard_configs(
            skip=skip,
            limit=limit,
            user_id=user_id
        )
        return configs
    except Exception as e:
        logger.error(f"Failed to list dashboard configs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard configs")


@router.post("/config", response_model=DashboardConfigResponse)
async def create_dashboard_config(
    config: DashboardConfigCreate,
    db: Session = Depends(get_db)
):
    """
    创建仪表板配置
    
    Args:
        config: 配置创建数据
        db: 数据库会话
        
    Returns:
        DashboardConfigResponse: 创建的配置
    """
    try:
        dashboard_service = DashboardService(db)
        created_config = await dashboard_service.create_dashboard_config(config)
        return created_config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create dashboard config: {e}")
        raise HTTPException(status_code=500, detail="Failed to create dashboard config")


@router.get("/config/{config_id}", response_model=DashboardConfigResponse)
async def get_dashboard_config(
    config_id: int = Path(..., description="配置ID"),
    db: Session = Depends(get_db)
):
    """
    获取指定仪表板配置详情
    
    Args:
        config_id: 配置ID
        db: 数据库会话
        
    Returns:
        DashboardConfigResponse: 配置详情
    """
    try:
        dashboard_service = DashboardService(db)
        config = await dashboard_service.get_dashboard_config(config_id)
        if not config:
            raise HTTPException(status_code=404, detail="Dashboard config not found")
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard config {config_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard config")


@router.put("/config/{config_id}", response_model=DashboardConfigResponse)
async def update_dashboard_config(
    config_id: int = Path(..., description="配置ID"),
    config_update: DashboardConfigUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """
    更新仪表板配置
    
    Args:
        config_id: 配置ID
        config_update: 配置更新数据
        db: 数据库会话
        
    Returns:
        DashboardConfigResponse: 更新后的配置
    """
    try:
        dashboard_service = DashboardService(db)
        updated_config = await dashboard_service.update_dashboard_config(config_id, config_update)
        if not updated_config:
            raise HTTPException(status_code=404, detail="Dashboard config not found")
        return updated_config
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update dashboard config {config_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update dashboard config")


@router.delete("/config/{config_id}")
async def delete_dashboard_config(
    config_id: int = Path(..., description="配置ID"),
    db: Session = Depends(get_db)
):
    """
    删除仪表板配置
    
    Args:
        config_id: 配置ID
        db: 数据库会话
        
    Returns:
        dict: 删除结果
    """
    try:
        dashboard_service = DashboardService(db)
        success = await dashboard_service.delete_dashboard_config(config_id)
        if not success:
            raise HTTPException(status_code=404, detail="Dashboard config not found")
        return {"message": "Dashboard config deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete dashboard config {config_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete dashboard config")


# 仪表板模板
@router.get("/templates", response_model=List[DashboardTemplateResponse])
async def list_dashboard_templates(
    dashboard_type: Optional[str] = Query(None, description="仪表板类型"),
    db: Session = Depends(get_db)
):
    """
    获取仪表板模板列表
    
    Args:
        dashboard_type: 仪表板类型过滤
        db: 数据库会话
        
    Returns:
        List[DashboardTemplateResponse]: 模板列表
    """
    try:
        dashboard_service = DashboardService(db)
        templates = await dashboard_service.list_dashboard_templates(dashboard_type)
        return templates
    except Exception as e:
        logger.error(f"Failed to list dashboard templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard templates")


@router.post("/templates/{template_id}/create", response_model=DashboardResponse)
async def create_dashboard_from_template(
    template_id: str = Path(..., description="模板ID"),
    name: str = Body(..., description="仪表板名称"),
    description: Optional[str] = Body(None, description="仪表板描述"),
    db: Session = Depends(get_db)
):
    """
    从模板创建仪表板
    
    Args:
        template_id: 模板ID
        name: 仪表板名称
        description: 仪表板描述
        db: 数据库会话
        
    Returns:
        DashboardResponse: 创建的仪表板
    """
    try:
        dashboard_service = DashboardService(db)
        dashboard = await dashboard_service.create_dashboard_from_template(
            template_id, name, description
        )
        return dashboard
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create dashboard from template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create dashboard from template")


# 仪表板操作
@router.post("/{dashboard_id}/clone", response_model=DashboardResponse)
async def clone_dashboard(
    dashboard_id: int = Path(..., description="仪表板ID"),
    name: str = Body(..., description="新仪表板名称"),
    description: Optional[str] = Body(None, description="新仪表板描述"),
    db: Session = Depends(get_db)
):
    """
    克隆仪表板
    
    Args:
        dashboard_id: 仪表板ID
        name: 新仪表板名称
        description: 新仪表板描述
        db: 数据库会话
        
    Returns:
        DashboardResponse: 克隆的仪表板
    """
    try:
        dashboard_service = DashboardService(db)
        cloned_dashboard = await dashboard_service.clone_dashboard(
            dashboard_id, name, description
        )
        if not cloned_dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        return cloned_dashboard
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clone dashboard {dashboard_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to clone dashboard")


@router.post("/{dashboard_id}/share")
async def share_dashboard(
    dashboard_id: int = Path(..., description="仪表板ID"),
    request: DashboardShareRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    分享仪表板
    
    Args:
        dashboard_id: 仪表板ID
        request: 分享请求
        db: 数据库会话
        
    Returns:
        dict: 分享结果
    """
    try:
        dashboard_service = DashboardService(db)
        result = await dashboard_service.share_dashboard(dashboard_id, request)
        if not result:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to share dashboard {dashboard_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to share dashboard")


@router.post("/{dashboard_id}/export")
async def export_dashboard(
    dashboard_id: int = Path(..., description="仪表板ID"),
    request: DashboardExportRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    导出仪表板
    
    Args:
        dashboard_id: 仪表板ID
        request: 导出请求
        db: 数据库会话
        
    Returns:
        dict: 导出结果
    """
    try:
        dashboard_service = DashboardService(db)
        result = await dashboard_service.export_dashboard(dashboard_id, request)
        if not result:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export dashboard {dashboard_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to export dashboard")


@router.post("/import", response_model=DashboardResponse)
async def import_dashboard(
    request: DashboardImportRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    导入仪表板
    
    Args:
        request: 导入请求
        db: 数据库会话
        
    Returns:
        DashboardResponse: 导入的仪表板
    """
    try:
        dashboard_service = DashboardService(db)
        dashboard = await dashboard_service.import_dashboard(request)
        return dashboard
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to import dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to import dashboard")


# 仪表板数据
@router.get("/{dashboard_id}/data")
async def get_dashboard_data(
    dashboard_id: int = Path(..., description="仪表板ID"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    refresh: bool = Query(False, description="是否强制刷新"),
    db: Session = Depends(get_db)
):
    """
    获取仪表板数据
    
    Args:
        dashboard_id: 仪表板ID
        start_time: 开始时间
        end_time: 结束时间
        refresh: 是否强制刷新
        db: 数据库会话
        
    Returns:
        dict: 仪表板数据
    """
    try:
        # 设置默认时间范围
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        dashboard_service = DashboardService(db)
        data = await dashboard_service.get_dashboard_data(
            dashboard_id=dashboard_id,
            start_time=start_time,
            end_time=end_time,
            refresh=refresh
        )
        if not data:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard data for dashboard {dashboard_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")


@router.get("/{dashboard_id}/widgets/{widget_id}/data")
async def get_widget_data(
    dashboard_id: int = Path(..., description="仪表板ID"),
    widget_id: int = Path(..., description="组件ID"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    refresh: bool = Query(False, description="是否强制刷新"),
    db: Session = Depends(get_db)
):
    """
    获取组件数据
    
    Args:
        dashboard_id: 仪表板ID
        widget_id: 组件ID
        start_time: 开始时间
        end_time: 结束时间
        refresh: 是否强制刷新
        db: 数据库会话
        
    Returns:
        dict: 组件数据
    """
    try:
        # 设置默认时间范围
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        dashboard_service = DashboardService(db)
        data = await dashboard_service.get_widget_data(
            dashboard_id=dashboard_id,
            widget_id=widget_id,
            start_time=start_time,
            end_time=end_time,
            refresh=refresh
        )
        if not data:
            raise HTTPException(status_code=404, detail="Widget not found")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get widget data for widget {widget_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve widget data")