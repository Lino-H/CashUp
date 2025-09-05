"""
策略管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from ..schemas.strategy import (
    StrategyInfo, StrategyCreate, StrategyUpdate, StrategyResponse, 
    StrategyListResponse, StrategyTemplateRequest
)
from ...services.strategy_service import StrategyService
from ...utils.logger import get_logger

router = APIRouter()
security = HTTPBearer()
logger = get_logger(__name__)

@router.get("/", response_model=StrategyListResponse)
async def get_strategies(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    search: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """获取策略列表"""
    try:
        strategy_service = StrategyService(db)
        strategies, total = await strategy_service.get_strategies(
            skip=skip, 
            limit=limit, 
            status=status, 
            search=search
        )
        
        return StrategyListResponse(
            strategies=[StrategyResponse.from_orm(strategy) for strategy in strategies],
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"获取策略列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取策略列表失败"
        )

@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """获取策略详情"""
    try:
        strategy_service = StrategyService(db)
        strategy = await strategy_service.get_strategy_by_id(strategy_id)
        
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="策略不存在"
            )
        
        return StrategyResponse.from_orm(strategy)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取策略详情失败"
        )

@router.post("/", response_model=StrategyResponse)
async def create_strategy(
    strategy_data: StrategyCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """创建策略"""
    try:
        strategy_service = StrategyService(db)
        
        # 验证策略代码
        validation_result = strategy_service.validate_strategy_code(strategy_data.code)
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"策略代码无效: {'; '.join(validation_result['errors'])}"
            )
        
        # 创建策略
        strategy = await strategy_service.create_strategy(strategy_data)
        
        logger.info(f"策略创建成功: {strategy.name}")
        return StrategyResponse.from_orm(strategy)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建策略失败"
        )

@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: int,
    strategy_data: StrategyUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """更新策略"""
    try:
        strategy_service = StrategyService(db)
        strategy = await strategy_service.get_strategy_by_id(strategy_id)
        
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="策略不存在"
            )
        
        # 如果更新代码，需要验证
        if "code" in strategy_data.dict(exclude_unset=True):
            validation_result = strategy_service.validate_strategy_code(strategy_data.code)
            if not validation_result["valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"策略代码无效: {'; '.join(validation_result['errors'])}"
                )
        
        # 更新策略
        updated_strategy = await strategy_service.update_strategy(strategy_id, strategy_data)
        
        logger.info(f"策略更新成功: {updated_strategy.name}")
        return StrategyResponse.from_orm(updated_strategy)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新策略失败"
        )

@router.delete("/{strategy_id}")
async def delete_strategy(
    strategy_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """删除策略"""
    try:
        strategy_service = StrategyService(db)
        strategy = await strategy_service.get_strategy_by_id(strategy_id)
        
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="策略不存在"
            )
        
        # 删除策略
        await strategy_service.delete_strategy(strategy_id)
        
        logger.info(f"策略删除成功: {strategy.name}")
        return {"message": "策略删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除策略失败"
        )

@router.post("/{strategy_id}/start")
async def start_strategy(
    strategy_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """启动策略"""
    try:
        strategy_service = StrategyService(db)
        result = await strategy_service.start_strategy(strategy_id)
        
        if result:
            return {"message": "策略启动成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="策略启动失败"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="启动策略失败"
        )

@router.post("/{strategy_id}/stop")
async def stop_strategy(
    strategy_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """停止策略"""
    try:
        strategy_service = StrategyService(db)
        result = await strategy_service.stop_strategy(strategy_id)
        
        if result:
            return {"message": "策略停止成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="策略停止失败"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="停止策略失败"
        )

@router.post("/{strategy_id}/reload")
async def reload_strategy(
    strategy_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """重新加载策略"""
    try:
        strategy_service = StrategyService(db)
        result = await strategy_service.reload_strategy(strategy_id)
        
        if result:
            return {"message": "策略重新加载成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="策略重新加载失败"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新加载策略失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重新加载策略失败"
        )

@router.get("/{strategy_id}/performance")
async def get_strategy_performance(
    strategy_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """获取策略性能"""
    try:
        strategy_service = StrategyService(db)
        performance = await strategy_service.get_strategy_performance(strategy_id)
        
        return performance
        
    except Exception as e:
        logger.error(f"获取策略性能失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取策略性能失败"
        )

@router.post("/templates")
async def create_strategy_template(
    template_request: StrategyTemplateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """创建策略模板"""
    try:
        strategy_service = StrategyService(db)
        template_code = strategy_service.create_strategy_template(
            template_request.strategy_name,
            template_request.strategy_type
        )
        
        return {
            "template_code": template_code,
            "strategy_name": template_request.strategy_name,
            "strategy_type": template_request.strategy_type
        }
        
    except Exception as e:
        logger.error(f"创建策略模板失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建策略模板失败"
        )

@router.get("/templates/types")
async def get_strategy_templates(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """获取策略模板类型"""
    try:
        strategy_service = StrategyService(db)
        template_types = strategy_service.get_strategy_template_types()
        
        return {"template_types": template_types}
        
    except Exception as e:
        logger.error(f"获取策略模板类型失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取策略模板类型失败"
        )

@router.post("/upload")
async def upload_strategy_file(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """上传策略文件"""
    try:
        strategy_service = StrategyService(db)
        
        # 读取文件内容
        content = await file.read()
        code = content.decode("utf-8")
        
        # 验证策略代码
        validation_result = strategy_service.validate_strategy_code(code)
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"策略代码无效: {'; '.join(validation_result['errors'])}"
            )
        
        # 创建策略
        strategy_data = StrategyCreate(
            name=file.filename.replace(".py", ""),
            code=code,
            description=f"上传的策略文件: {file.filename}",
            type="custom"
        )
        
        strategy = await strategy_service.create_strategy(strategy_data)
        
        logger.info(f"策略文件上传成功: {file.filename}")
        return StrategyResponse.from_orm(strategy)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传策略文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="上传策略文件失败"
        )

# 导入依赖函数
from ...database.connection import get_db