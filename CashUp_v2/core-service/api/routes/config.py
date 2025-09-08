"""
配置管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import random

from schemas.config import ConfigCreate, ConfigUpdate, ConfigResponse, ConfigListResponse
from services.config import ConfigService
from database.connection import get_db
from utils.logger import get_logger
from auth.dependencies import get_current_user, get_current_active_user

router = APIRouter()
security = HTTPBearer()
logger = get_logger(__name__)

@router.get("/", response_model=ConfigListResponse)
async def get_configs(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    search: Optional[str] = None,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取配置列表"""
    try:
        config_service = ConfigService(db)
        configs, total = await config_service.get_configs(
            skip=skip, 
            limit=limit, 
            category=category, 
            search=search
        )
        
        return ConfigListResponse(
            configs=[ConfigResponse.from_orm(config) for config in configs],
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"获取配置列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取配置列表失败"
        )

@router.get("/{config_id}", response_model=ConfigResponse)
async def get_config(
    config_id: int,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取配置详情"""
    try:
        config_service = ConfigService(db)
        config = await config_service.get_config_by_id(config_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置不存在"
            )
        
        # 检查权限：用户配置只能被创建者查看，系统配置管理员可查看
        if config.user_id and config.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看此配置"
            )
        
        return ConfigResponse.from_orm(config)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取配置详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取配置详情失败"
        )

@router.post("/", response_model=ConfigResponse)
async def create_config(
    config_data: ConfigCreate,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建配置"""
    try:
        config_service = ConfigService(db)
        
        # 检查配置键是否已存在
        existing_config = await config_service.get_config_by_key(config_data.key)
        if existing_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="配置键已存在"
            )
        
        # 如果是系统配置，只有管理员可以创建
        if config_data.is_system and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权创建系统配置"
            )
        
        # 创建配置
        config = await config_service.create_config(config_data, current_user.id)
        
        logger.info(f"配置创建成功: {config.key}")
        return ConfigResponse.from_orm(config)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建配置失败"
        )

@router.put("/{config_id}", response_model=ConfigResponse)
async def update_config(
    config_id: int,
    config_data: ConfigUpdate,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新配置"""
    try:
        config_service = ConfigService(db)
        config = await config_service.get_config_by_id(config_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置不存在"
            )
        
        # 检查权限
        if config.user_id and config.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权更新此配置"
            )
        
        # 系统配置只有管理员可以更新
        if config.is_system and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权更新系统配置"
            )
        
        # 更新配置
        updated_config = await config_service.update_config(config_id, config_data)
        
        logger.info(f"配置更新成功: {updated_config.key}")
        return ConfigResponse.from_orm(updated_config)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新配置失败"
        )

@router.delete("/{config_id}")
async def delete_config(
    config_id: int,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除配置"""
    try:
        config_service = ConfigService(db)
        config = await config_service.get_config_by_id(config_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置不存在"
            )
        
        # 检查权限
        if config.user_id and config.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此配置"
            )
        
        # 系统配置只有管理员可以删除
        if config.is_system and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除系统配置"
            )
        
        # 删除配置
        await config_service.delete_config(config_id)
        
        logger.info(f"配置删除成功: {config.key}")
        return {"message": "配置删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除配置失败"
        )

@router.get("/by-key/{key}", response_model=ConfigResponse)
async def get_config_by_key(
    key: str,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """根据键获取配置"""
    try:
        config_service = ConfigService(db)
        config = await config_service.get_config_by_key(key)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置不存在"
            )
        
        # 检查权限
        if config.user_id and config.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看此配置"
            )
        
        return ConfigResponse.from_orm(config)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取配置失败"
        )

@router.get("/category/{category}", response_model=ConfigListResponse)
async def get_configs_by_category(
    category: str,
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """根据分类获取配置"""
    try:
        config_service = ConfigService(db)
        configs, total = await config_service.get_configs_by_category(
            category, skip=skip, limit=limit
        )
        
        # 过滤用户有权限查看的配置
        accessible_configs = []
        for config in configs:
            if config.user_id is None or config.user_id == current_user.id or current_user.role == "admin":
                accessible_configs.append(config)
        
        return ConfigListResponse(
            configs=[ConfigResponse.from_orm(config) for config in accessible_configs],
            total=len(accessible_configs),
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"获取分类配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取分类配置失败"
        )

@router.post("/batch")
async def batch_update_configs(
    configs: List[Dict[str, Any]],
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """批量更新配置"""
    try:
        config_service = ConfigService(db)
        updated_configs = []
        
        for config_data in configs:
            config_id = config_data.get('id')
            if not config_id:
                continue
            
            config = await config_service.get_config_by_id(config_id)
            if not config:
                continue
            
            # 检查权限
            if config.user_id and config.user_id != current_user.id and current_user.role != "admin":
                continue
            
            # 系统配置只有管理员可以更新
            if config.is_system and current_user.role != "admin":
                continue
            
            # 更新配置
            update_data = {k: v for k, v in config_data.items() if k != 'id'}
            updated_config = await config_service.update_config(config_id, update_data)
            updated_configs.append(updated_config)
        
        logger.info(f"批量更新配置成功: {len(updated_configs)} 个配置")
        return {
            "message": f"批量更新成功",
            "updated_count": len(updated_configs),
            "configs": [ConfigResponse.from_orm(config) for config in updated_configs]
        }
        
    except Exception as e:
        logger.error(f"批量更新配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量更新配置失败"
        )

@router.get("/my", response_model=ConfigListResponse)
async def get_my_configs(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户的配置"""
    try:
        config_service = ConfigService(db)
        configs, total = await config_service.get_user_configs(
            current_user.id, skip=skip, limit=limit, category=category
        )
        
        return ConfigListResponse(
            configs=[ConfigResponse.from_orm(config) for config in configs],
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"获取用户配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户配置失败"
        )

# 分析数据API端点

@router.get("/analysis/technical")
async def get_technical_analysis(
    current_user = Depends(get_current_active_user)
):
    """获取技术分析数据"""
    try:
        # 模拟真实技术分析数据
        technical_data = {
            "score": random.randint(70, 95),
            "indicators": {
                "ma5": random.uniform(45.2, 52.8),
                "ma10": random.uniform(44.8, 53.2),
                "ma20": random.uniform(43.5, 54.5),
                "ma50": random.uniform(42.0, 56.0),
                "macd": random.uniform(-2.5, 2.5),
                "signal": random.uniform(-2.3, 2.3),
                "histogram": random.uniform(-0.5, 0.5),
                "rsi": random.uniform(30, 70),
                "kdj_k": random.uniform(20, 80),
                "kdj_d": random.uniform(25, 75),
                "kdj_j": random.uniform(15, 85),
                "bb_upper": random.uniform(55, 65),
                "bb_middle": random.uniform(48, 58),
                "bb_lower": random.uniform(41, 51)
            },
            "trend": random.choice(["上涨", "下跌", "盘整"]),
            "signal": random.choice(["买入", "卖出", "持有"]),
            "last_updated": datetime.now().isoformat()
        }
        
        logger.info(f"获取技术分析数据成功: {current_user.username}")
        return technical_data
        
    except Exception as e:
        logger.error(f"获取技术分析数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取技术分析数据失败"
        )

@router.get("/analysis/fundamental")
async def get_fundamental_analysis(
    current_user = Depends(get_current_active_user)
):
    """获取基本面分析数据"""
    try:
        fundamental_data = {
            "score": random.randint(60, 90),
            "metrics": {
                "pe_ratio": random.uniform(10, 30),
                "pb_ratio": random.uniform(1.5, 5.0),
                "roe": random.uniform(8, 25),
                "roa": random.uniform(5, 15),
                "debt_ratio": random.uniform(20, 60),
                "current_ratio": random.uniform(1.2, 3.0),
                "quick_ratio": random.uniform(0.8, 2.5),
                "dividend_yield": random.uniform(2, 8)
            },
            "rating": random.choice(["AA", "A", "BBB", "BB", "B"]),
            "outlook": random.choice(["乐观", "中性", "谨慎"]),
            "last_updated": datetime.now().isoformat()
        }
        
        logger.info(f"获取基本面分析数据成功: {current_user.username}")
        return fundamental_data
        
    except Exception as e:
        logger.error(f"获取基本面分析数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取基本面分析数据失败"
        )

@router.get("/analysis/sentiment")
async def get_sentiment_analysis(
    current_user = Depends(get_current_active_user)
):
    """获取情绪分析数据"""
    try:
        sentiment_data = {
            "score": random.randint(65, 88),
            "indicators": {
                "market_sentiment": random.uniform(0.3, 0.7),
                "news_sentiment": random.uniform(0.4, 0.8),
                "social_media_sentiment": random.uniform(0.2, 0.9),
                "fear_greed_index": random.randint(20, 80),
                "put_call_ratio": random.uniform(0.6, 1.4),
                "volatility_index": random.uniform(15, 35)
            },
            "overall_sentiment": random.choice(["乐观", "中性", "悲观"]),
            "confidence": random.uniform(0.6, 0.95),
            "last_updated": datetime.now().isoformat()
        }
        
        logger.info(f"获取情绪分析数据成功: {current_user.username}")
        return sentiment_data
        
    except Exception as e:
        logger.error(f"获取情绪分析数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取情绪分析数据失败"
        )

@router.get("/analysis/risk")
async def get_risk_analysis(
    current_user = Depends(get_current_active_user)
):
    """获取风险分析数据"""
    try:
        risk_data = {
            "score": random.randint(55, 85),
            "metrics": {
                "var_95": random.uniform(0.02, 0.08),
                "var_99": random.uniform(0.03, 0.12),
                "sharpe_ratio": random.uniform(0.5, 2.5),
                "sortino_ratio": random.uniform(0.8, 3.0),
                "max_drawdown": random.uniform(0.05, 0.25),
                "beta": random.uniform(0.8, 1.5),
                "alpha": random.uniform(-0.1, 0.1),
                "information_ratio": random.uniform(0.3, 1.8)
            },
            "risk_level": random.choice(["低", "中", "高"]),
            "risk_alerts": [
                "市场波动率增加",
                "流动性风险上升",
                "集中度风险偏高"
            ],
            "last_updated": datetime.now().isoformat()
        }
        
        logger.info(f"获取风险分析数据成功: {current_user.username}")
        return risk_data
        
    except Exception as e:
        logger.error(f"获取风险分析数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取风险分析数据失败"
        )

@router.get("/trading/strategies/count")
async def get_strategies_count(
    current_user = Depends(get_current_active_user)
):
    """获取策略数量"""
    try:
        count = random.randint(10, 50)
        return {"count": count}
        
    except Exception as e:
        logger.error(f"获取策略数量失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取策略数量失败"
        )

@router.get("/automation/tasks/count")
async def get_automation_tasks_count(
    current_user = Depends(get_current_active_user)
):
    """获取自动化任务数量"""
    try:
        count = random.randint(5, 30)
        return {"count": count}
        
    except Exception as e:
        logger.error(f"获取自动化任务数量失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取自动化任务数量失败"
        )

@router.get("/scheduler/tasks/count")
async def get_scheduler_tasks_count(
    current_user = Depends(get_current_active_user)
):
    """获取计划任务数量"""
    try:
        count = random.randint(3, 20)
        return {"count": count}
        
    except Exception as e:
        logger.error(f"获取计划任务数量失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取计划任务数量失败"
        )

@router.get("/reports/count")
async def get_reports_count(
    current_user = Depends(get_current_active_user)
):
    """获取报告数量"""
    try:
        count = random.randint(10, 100)
        return {"count": count}
        
    except Exception as e:
        logger.error(f"获取报告数量失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取报告数量失败"
        )