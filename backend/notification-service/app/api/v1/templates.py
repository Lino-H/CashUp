#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 模板API路由

处理通知模板相关的API请求
"""

import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.auth import get_current_user
from ...models.template import TemplateType
from ...schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateListResponse,
    TemplateFilter,
    TemplateRender,
    TemplateRenderResponse,
    TemplatePreview,
    TemplatePreviewResponse,
    TemplateClone,
    TemplateCloneResponse,
    TemplateValidation,
    TemplateValidationResponse,
    TemplateStatsResponse,
    TemplateBulkOperation,
    TemplateBulkOperationResponse,
    TemplateExport,
    TemplateExportResponse,
    TemplateImport,
    TemplateImportResponse
)
from ...schemas.common import (
    BaseResponse,
    PaginationParams
)
from ...services.template_service import TemplateService
from ...services.websocket_service import websocket_service

import logging
import json
import io

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()

# 依赖注入
def get_template_service() -> TemplateService:
    return TemplateService()


@router.post("/", response_model=TemplateResponse)
async def create_template(
    template: TemplateCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """
    创建模板
    
    Args:
        template: 模板创建请求
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        service: 模板服务
        
    Returns:
        TemplateResponse: 创建的模板信息
    """
    try:
        # 创建模板
        created_template = await service.create_template(
            db=db,
            template_data=template,
            user_id=current_user["user_id"]
        )
        
        # 发送WebSocket通知
        background_tasks.add_task(
            websocket_service.send_system_message,
            {
                "type": "template_created",
                "template_id": str(created_template.id),
                "template_name": created_template.name,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return TemplateResponse.from_orm(created_template)
        
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=TemplateListResponse)
async def get_templates(
    pagination: PaginationParams = Depends(),
    filters: TemplateFilter = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """
    获取模板列表
    
    Args:
        pagination: 分页参数
        filters: 过滤参数
        db: 数据库会话
        current_user: 当前用户
        service: 模板服务
        
    Returns:
        TemplateListResponse: 模板列表
    """
    try:
        # 获取模板列表
        templates, total = await service.get_templates(
            db=db,
            skip=pagination.skip,
            limit=pagination.limit,
            filters=filters
        )
        
        return TemplateListResponse(
            items=[TemplateResponse.from_orm(t) for t in templates],
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=(total + pagination.size - 1) // pagination.size
        )
        
    except Exception as e:
        logger.error(f"Error getting templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """
    获取单个模板
    
    Args:
        template_id: 模板ID
        db: 数据库会话
        current_user: 当前用户
        service: 模板服务
        
    Returns:
        TemplateResponse: 模板信息
    """
    try:
        template = await service.get_template(db, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return TemplateResponse.from_orm(template)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template {template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: uuid.UUID,
    template_update: TemplateUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """
    更新模板
    
    Args:
        template_id: 模板ID
        template_update: 更新数据
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        service: 模板服务
        
    Returns:
        TemplateResponse: 更新后的模板信息
    """
    try:
        updated_template = await service.update_template(
            db=db,
            template_id=template_id,
            template_data=template_update
        )
        
        if not updated_template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # 发送WebSocket通知
        background_tasks.add_task(
            websocket_service.send_system_message,
            {
                "type": "template_updated",
                "template_id": str(template_id),
                "template_name": updated_template.name,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return TemplateResponse.from_orm(updated_template)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template {template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{template_id}", response_model=BaseResponse)
async def delete_template(
    template_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """
    删除模板
    
    Args:
        template_id: 模板ID
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        service: 模板服务
        
    Returns:
        BaseResponse: 删除结果
    """
    try:
        success = await service.delete_template(db, template_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # 发送WebSocket通知
        background_tasks.add_task(
            websocket_service.send_system_message,
            {
                "type": "template_deleted",
                "template_id": str(template_id),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return BaseResponse(
            success=True,
            message="Template deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template {template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/render", response_model=TemplateRenderResponse)
async def render_template(
    render_request: TemplateRender,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """
    渲染模板
    
    Args:
        render_request: 渲染请求
        db: 数据库会话
        current_user: 当前用户
        service: 模板服务
        
    Returns:
        TemplateRenderResponse: 渲染结果
    """
    try:
        result = await service.render_template(
            db=db,
            template_id=render_request.template_id,
            variables=render_request.variables,
            output_format=render_request.output_format
        )
        
        return TemplateRenderResponse(**result)
        
    except Exception as e:
        logger.error(f"Error rendering template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview", response_model=TemplatePreviewResponse)
async def preview_template(
    preview_request: TemplatePreview,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """
    预览模板
    
    Args:
        preview_request: 预览请求
        db: 数据库会话
        current_user: 当前用户
        service: 模板服务
        
    Returns:
        TemplatePreviewResponse: 预览结果
    """
    try:
        result = await service.preview_template(
            db=db,
            template_id=preview_request.template_id,
            variables=preview_request.variables
        )
        
        return TemplatePreviewResponse(**result)
        
    except Exception as e:
        logger.error(f"Error previewing template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{template_id}/clone", response_model=TemplateCloneResponse)
async def clone_template(
    template_id: uuid.UUID,
    clone_request: TemplateClone,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """
    克隆模板
    
    Args:
        template_id: 模板ID
        clone_request: 克隆请求
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        service: 模板服务
        
    Returns:
        TemplateCloneResponse: 克隆结果
    """
    try:
        cloned_template = await service.clone_template(
            db=db,
            template_id=template_id,
            new_name=clone_request.new_name,
            new_description=clone_request.new_description,
            user_id=current_user["user_id"]
        )
        
        # 发送WebSocket通知
        background_tasks.add_task(
            websocket_service.send_system_message,
            {
                "type": "template_cloned",
                "original_template_id": str(template_id),
                "new_template_id": str(cloned_template.id),
                "new_template_name": cloned_template.name,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return TemplateCloneResponse(
            template=TemplateResponse.from_orm(cloned_template),
            message="Template cloned successfully"
        )
        
    except Exception as e:
        logger.error(f"Error cloning template {template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", response_model=TemplateValidationResponse)
async def validate_template(
    validation_request: TemplateValidation,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """
    验证模板
    
    Args:
        validation_request: 验证请求
        db: 数据库会话
        current_user: 当前用户
        service: 模板服务
        
    Returns:
        TemplateValidationResponse: 验证结果
    """
    try:
        result = await service.validate_template(
            subject=validation_request.subject,
            content=validation_request.content,
            html_content=validation_request.html_content,
            variables=validation_request.variables
        )
        
        return TemplateValidationResponse(**result)
        
    except Exception as e:
        logger.error(f"Error validating template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=TemplateStatsResponse)
async def get_template_stats(
    start_date: Optional[datetime] = Query(None, description="统计开始日期"),
    end_date: Optional[datetime] = Query(None, description="统计结束日期"),
    template_type: Optional[TemplateType] = Query(None, description="模板类型过滤"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """
    获取模板统计信息
    
    Args:
        start_date: 统计开始日期
        end_date: 统计结束日期
        template_type: 模板类型过滤
        db: 数据库会话
        current_user: 当前用户
        service: 模板服务
        
    Returns:
        TemplateStatsResponse: 统计信息
    """
    try:
        stats = await service.get_template_stats(
            db=db,
            start_date=start_date,
            end_date=end_date,
            template_type=template_type
        )
        
        return TemplateStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting template stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk", response_model=TemplateBulkOperationResponse)
async def bulk_template_operation(
    bulk_request: TemplateBulkOperation,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """
    批量模板操作
    
    Args:
        bulk_request: 批量操作请求
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        service: 模板服务
        
    Returns:
        TemplateBulkOperationResponse: 批量操作结果
    """
    try:
        # 这里应该实现实际的批量操作逻辑
        # 为了演示，返回模拟数据
        result = {
            "operation": bulk_request.operation,
            "total_count": len(bulk_request.template_ids),
            "success_count": len(bulk_request.template_ids),
            "failed_count": 0,
            "errors": [],
            "message": f"Bulk {bulk_request.operation} completed successfully"
        }
        
        # 发送WebSocket通知
        background_tasks.add_task(
            websocket_service.send_system_message,
            {
                "type": "template_bulk_operation_completed",
                "operation": bulk_request.operation,
                "success_count": result["success_count"],
                "failed_count": result["failed_count"],
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return TemplateBulkOperationResponse(**result)
        
    except Exception as e:
        logger.error(f"Error performing bulk template operation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export", response_model=TemplateExportResponse)
async def export_templates(
    export_request: TemplateExport,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """
    导出模板
    
    Args:
        export_request: 导出请求
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        service: 模板服务
        
    Returns:
        TemplateExportResponse: 导出结果
    """
    try:
        # 这里应该实现实际的导出逻辑
        # 为了演示，返回模拟数据
        export_id = str(uuid.uuid4())
        
        # 添加后台任务处理导出
        background_tasks.add_task(
            _process_template_export,
            export_id,
            export_request,
            current_user["user_id"]
        )
        
        return TemplateExportResponse(
            export_id=export_id,
            status="processing",
            message="Template export task has been queued",
            estimated_completion=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error exporting templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import", response_model=TemplateImportResponse)
async def import_templates(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """
    导入模板
    
    Args:
        file: 上传的文件
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        service: 模板服务
        
    Returns:
        TemplateImportResponse: 导入结果
    """
    try:
        # 检查文件类型
        if not file.filename.endswith(('.json', '.csv', '.xlsx')):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Please upload JSON, CSV, or Excel files."
            )
        
        # 读取文件内容
        content = await file.read()
        
        # 这里应该实现实际的导入逻辑
        # 为了演示，返回模拟数据
        import_id = str(uuid.uuid4())
        
        # 添加后台任务处理导入
        if background_tasks:
            background_tasks.add_task(
                _process_template_import,
                import_id,
                content,
                file.filename,
                current_user["user_id"]
            )
        
        return TemplateImportResponse(
            import_id=import_id,
            status="processing",
            total_count=0,
            success_count=0,
            failed_count=0,
            errors=[],
            message="Template import task has been queued"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _process_template_export(
    export_id: str,
    export_request: TemplateExport,
    user_id: str
):
    """
    处理模板导出任务
    
    Args:
        export_id: 导出ID
        export_request: 导出请求
        user_id: 用户ID
    """
    try:
        # 这里应该实现实际的导出逻辑
        import asyncio
        await asyncio.sleep(5)  # 模拟处理时间
        
        # 发送完成通知
        await websocket_service.send_user_message(
            user_id,
            {
                "type": "template_export_completed",
                "export_id": export_id,
                "download_url": f"/api/v1/templates/exports/{export_id}/download",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing template export {export_id}: {str(e)}")
        
        # 发送失败通知
        await websocket_service.send_user_message(
            user_id,
            {
                "type": "template_export_failed",
                "export_id": export_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


async def _process_template_import(
    import_id: str,
    content: bytes,
    filename: str,
    user_id: str
):
    """
    处理模板导入任务
    
    Args:
        import_id: 导入ID
        content: 文件内容
        filename: 文件名
        user_id: 用户ID
    """
    try:
        # 这里应该实现实际的导入逻辑
        import asyncio
        await asyncio.sleep(5)  # 模拟处理时间
        
        # 发送完成通知
        await websocket_service.send_user_message(
            user_id,
            {
                "type": "template_import_completed",
                "import_id": import_id,
                "success_count": 5,
                "failed_count": 0,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing template import {import_id}: {str(e)}")
        
        # 发送失败通知
        await websocket_service.send_user_message(
            user_id,
            {
                "type": "template_import_failed",
                "import_id": import_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )