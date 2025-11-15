"""
配置管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
import random

from schemas.config import ConfigCreate, ConfigUpdate, ConfigResponse, ConfigListResponse
from services.config import ConfigService
from database.connection import get_db
from utils.logger import get_logger
from typing import Any

router = APIRouter()
security = HTTPBearer()
logger = get_logger(__name__)

@router.get("/", response_model=ConfigListResponse)
async def get_configs(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    search: Optional[str] = None,
    current_user: Any | None = None,
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
    current_user: Any | None = None,
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
        # 简化权限：个人系统不校验用户角色
        # if config.user_id and current_user is not None and config.user_id != getattr(current_user, 'id', None):
        #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看此配置")
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
    current_user: Any | None = None,
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
        # 个人系统忽略管理员限制
        
        # 创建配置
        config = await config_service.create_config(config_data, None)
        
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
    current_user: Any | None = None,
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
        # 个人系统忽略用户校验
        
        # 系统配置只有管理员可以更新
        # 个人系统忽略管理员限制
        
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
    current_user: Any | None = None,
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
        # 个人系统忽略用户校验
        
        # 系统配置只有管理员可以删除
        # 个人系统忽略管理员限制
        
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
    current_user: Any | None = None,
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
        # 个人系统忽略校验
        
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
    current_user: Any | None = None,
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
    current_user: Any | None = None,
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
    current_user: Any | None = None,
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
    current_user: Any | None = None
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
    current_user: Any | None = None
):
    """获取基本面分析数据"""
    try:
        fundamental_data = {
            "score": random.randint(60, 90),
            "indicators": {
                "pe_ratio": random.uniform(10, 30),
                "pb_ratio": random.uniform(1.5, 5.0),
                "roe": random.uniform(8, 25) / 100,  # 转换为小数
                "roa": random.uniform(5, 15) / 100,  # 转换为小数
                "debt_to_equity": random.uniform(20, 60) / 100,  # 转换为小数
                "current_ratio": random.uniform(1.2, 3.0),
                "quick_ratio": random.uniform(0.8, 2.5),
                "dividend_yield": random.uniform(2, 8) / 100,  # 转换为小数
                "eps": random.uniform(2, 10),
                "revenue_growth": random.uniform(5, 20) / 100,  # 转换为小数
                "profit_margin": random.uniform(10, 30) / 100,  # 转换为小数
                "operating_margin": random.uniform(15, 35) / 100  # 转换为小数
            },
            "overall_rating": random.choice(["A", "B", "C", "D"]),
            "recommendation": random.choice(["强烈买入", "买入", "持有", "卖出", "强烈卖出"]),
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
    current_user: Any | None = None
):
    """获取情绪分析数据"""
    try:
        sentiment_data = {
            "score": random.randint(65, 88),
            "sentiment": {
                "market_sentiment": random.choice(["极度乐观", "非常乐观", "乐观", "偏乐观", "中性", "偏悲观", "悲观", "非常悲观", "极度悲观"]),
                "social_sentiment": random.choice(["极度乐观", "非常乐观", "乐观", "偏乐观", "中性", "偏悲观", "悲观", "非常悲观", "极度悲观"]),
                "news_sentiment": random.choice(["极度乐观", "非常乐观", "乐观", "偏乐观", "中性", "偏悲观", "悲观", "非常悲观", "极度悲观"]),
                "analyst_sentiment": random.choice(["强烈买入", "买入", "持有", "卖出", "强烈卖出"]),
                "fear_greed_index": random.randint(20, 80),
                "social_media_metrics": {
                    "mentions": random.randint(1000, 50000),
                    "sentiment_score": random.uniform(-1, 1),
                    "engagement_rate": random.uniform(0.01, 0.1),
                    "positive_mentions": random.randint(500, 25000),
                    "negative_mentions": random.randint(100, 10000),
                    "neutral_mentions": random.randint(500, 15000)
                },
                "news_metrics": {
                    "articles_count": random.randint(50, 500),
                    "positive_articles": random.randint(10, 250),
                    "negative_articles": random.randint(5, 150),
                    "neutral_articles": random.randint(10, 200),
                    "sentiment_score": random.uniform(-1, 1)
                },
                "analyst_ratings": {
                    "strong_buy": random.randint(5, 25),
                    "buy": random.randint(10, 30),
                    "hold": random.randint(15, 40),
                    "sell": random.randint(3, 15),
                    "strong_sell": random.randint(1, 10),
                    "avg_rating": random.uniform(1.5, 4.5),
                    "target_price": random.uniform(100, 200),
                    "current_price": random.uniform(80, 180),
                    "upside_potential": random.uniform(-10, 50)
                },
                "recent_events": [
                    {
                        "date": (datetime.now() - timedelta(days=1)).isoformat(),
                        "event": "重要财报发布",
                        "impact": random.choice(["positive", "negative", "neutral"]),
                        "sentiment_change": random.uniform(-0.1, 0.1)
                    },
                    {
                        "date": (datetime.now() - timedelta(days=3)).isoformat(),
                        "event": "重大战略合作",
                        "impact": random.choice(["positive", "negative", "neutral"]),
                        "sentiment_change": random.uniform(-0.1, 0.1)
                    },
                    {
                        "date": (datetime.now() - timedelta(days=7)).isoformat(),
                        "event": "行业政策变化",
                        "impact": random.choice(["positive", "negative", "neutral"]),
                        "sentiment_change": random.uniform(-0.1, 0.1)
                    }
                ]
            },
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
    current_user: Any | None = None,
    range: str = "1M"
):
    """获取风险分析数据"""
    try:
        risk_data = {
            "score": random.randint(55, 85),
            "metrics": {
                "market_risk": random.uniform(2, 9),
                "credit_risk": random.uniform(1, 8),
                "liquidity_risk": random.uniform(1, 7),
                "operational_risk": random.uniform(1, 6),
                "volatility_risk": random.uniform(2, 8),
                "concentration_risk": random.uniform(1, 7),
                "correlation_risk": random.uniform(1, 6),
                "regulatory_risk": random.uniform(1, 5),
                "technological_risk": random.uniform(1, 6)
            },
            "assessment": {
                "risk_level": random.choice(["low", "medium", "high", "critical"]),
                "risk_score": random.uniform(1, 10),
                "risk_factors": [
                    {
                        "factor": "市场风险",
                        "level": random.uniform(1, 10),
                        "description": "市场波动性导致的投资组合价值变化风险",
                        "mitigation": "多元化投资，设置止损点"
                    },
                    {
                        "factor": "信用风险",
                        "level": random.uniform(1, 10),
                        "description": "交易对手违约导致的损失风险",
                        "mitigation": "分散投资，信用风险评估"
                    },
                    {
                        "factor": "流动性风险",
                        "level": random.uniform(1, 10),
                        "description": "资产无法及时变现导致的损失风险",
                        "mitigation": "保持足够的流动性缓冲"
                    },
                    {
                        "factor": "操作风险",
                        "level": random.uniform(1, 10),
                        "description": "内部流程、人员、系统故障导致的风险",
                        "mitigation": "完善风控制度，定期审计"
                    },
                    {
                        "factor": "集中度风险",
                        "level": random.uniform(1, 10),
                        "description": "投资组合过度集中导致的风险",
                        "mitigation": "分散投资，控制单一资产比例"
                    }
                ],
                "var_metrics": {
                    "var_95": random.uniform(0.02, 0.08),
                    "var_99": random.uniform(0.03, 0.12),
                    "var_1d": random.uniform(0.001, 0.005),
                    "var_1w": random.uniform(0.01, 0.03),
                    "var_1m": random.uniform(0.05, 0.15)
                },
                "stress_test": {
                    "market_crash": random.uniform(0.1, 0.4),
                    "liquidity_crisis": random.uniform(0.05, 0.25),
                    "credit_event": random.uniform(0.02, 0.15),
                    "system_failure": random.uniform(0.01, 0.08)
                },
                "portfolio_metrics": {
                    "sharpe_ratio": random.uniform(0.5, 2.5),
                    "sortino_ratio": random.uniform(0.8, 3.0),
                    "max_drawdown": random.uniform(0.05, 0.25),
                    "calmar_ratio": random.uniform(0.5, 3.0),
                    "beta": random.uniform(0.8, 1.5),
                    "alpha": random.uniform(-0.1, 0.1),
                    "information_ratio": random.uniform(0.3, 1.8)
                },
                "recommendations": {
                    "risk_level": random.choice(["低风险", "中等风险", "高风险", "极高风险"]),
                    "actions": [
                        "定期重新评估投资组合风险",
                        "设置合理的止损点位",
                        "保持适当的多元化配置",
                        "密切关注市场变化"
                    ],
                    "monitoring": [
                        "每日监控VaR指标",
                        "定期进行压力测试",
                        "跟踪相关性和集中度",
                        "关注信用风险变化"
                    ]
                }
            },
            "last_updated": datetime.now().isoformat()
        }
        
        logger.info(f"获取风险分析数据成功: {current_user.username}, 时间范围: {range}")
        return risk_data
        
    except Exception as e:
        logger.error(f"获取风险分析数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取风险分析数据失败"
        )

@router.get("/trading/strategies/count")
async def get_strategies_count(
    current_user: Any | None = None
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
    current_user: Any | None = None
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
    current_user: Any | None = None
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
    current_user: Any | None = None
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