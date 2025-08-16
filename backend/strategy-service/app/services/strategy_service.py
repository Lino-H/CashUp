#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略服务业务逻辑

提供策略管理的核心业务逻辑，包括策略的创建、更新、删除、
查询等操作，以及策略执行和性能分析功能。
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime, timedelta
import logging

from ..models.strategy import Strategy, StrategyStatus, StrategyType
from ..schemas.strategy import (
    StrategyCreate, StrategyUpdate, StrategyQueryParams,
    StrategyResponse, StrategyListResponse
)
from ..core.cache import get_strategy_cache
from .backtest_service import BacktestService

logger = logging.getLogger(__name__)


class StrategyService:
    """
    策略服务类
    
    提供策略管理的核心业务逻辑
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.cache = get_strategy_cache()
        self.backtest_service = BacktestService(db)
    
    def create_strategy(self, strategy_data: StrategyCreate, user_id: int) -> StrategyResponse:
        """
        创建新策略
        
        Args:
            strategy_data: 策略创建数据
            user_id: 用户ID
            
        Returns:
            StrategyResponse: 创建的策略信息
        """
        try:
            # 创建策略实例
            strategy = Strategy(
                name=strategy_data.name,
                description=strategy_data.description,
                strategy_type=strategy_data.strategy_type,
                code=strategy_data.code,
                parameters=strategy_data.parameters,
                risk_config=strategy_data.risk_config,
                symbols=strategy_data.symbols,
                timeframe=strategy_data.timeframe,
                initial_capital=strategy_data.initial_capital,
                max_positions=strategy_data.max_positions,
                user_id=user_id,
                status=StrategyStatus.DRAFT
            )
            
            # 保存到数据库
            self.db.add(strategy)
            self.db.commit()
            self.db.refresh(strategy)
            
            # 缓存策略数据
            self._cache_strategy(strategy)
            
            logger.info(f"策略创建成功: {strategy.id} - {strategy.name}")
            return StrategyResponse.from_orm(strategy)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建策略失败: {e}")
            raise
    
    def get_strategy(self, strategy_id: int, user_id: Optional[int] = None) -> Optional[StrategyResponse]:
        """
        获取策略详情
        
        Args:
            strategy_id: 策略ID
            user_id: 用户ID（用于权限检查）
            
        Returns:
            Optional[StrategyResponse]: 策略信息
        """
        try:
            # 先从缓存获取
            cached_data = self.cache.get_strategy_data(str(strategy_id))
            if cached_data:
                return StrategyResponse(**cached_data)
            
            # 从数据库查询
            query = self.db.query(Strategy).filter(Strategy.id == strategy_id)
            if user_id:
                query = query.filter(Strategy.user_id == user_id)
            
            strategy = query.first()
            if not strategy:
                return None
            
            # 缓存策略数据
            self._cache_strategy(strategy)
            
            return StrategyResponse.from_orm(strategy)
            
        except Exception as e:
            logger.error(f"获取策略失败: {e}")
            return None
    
    def update_strategy(self, strategy_id: int, strategy_data: StrategyUpdate, user_id: int) -> Optional[StrategyResponse]:
        """
        更新策略
        
        Args:
            strategy_id: 策略ID
            strategy_data: 更新数据
            user_id: 用户ID
            
        Returns:
            Optional[StrategyResponse]: 更新后的策略信息
        """
        try:
            # 查询策略
            strategy = self.db.query(Strategy).filter(
                and_(Strategy.id == strategy_id, Strategy.user_id == user_id)
            ).first()
            
            if not strategy:
                return None
            
            # 更新字段
            update_data = strategy_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(strategy, field, value)
            
            strategy.updated_at = datetime.utcnow()
            
            # 保存更改
            self.db.commit()
            self.db.refresh(strategy)
            
            # 更新缓存
            self._cache_strategy(strategy)
            
            logger.info(f"策略更新成功: {strategy.id} - {strategy.name}")
            return StrategyResponse.from_orm(strategy)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新策略失败: {e}")
            raise
    
    def delete_strategy(self, strategy_id: int, user_id: int) -> bool:
        """
        删除策略
        
        Args:
            strategy_id: 策略ID
            user_id: 用户ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            # 查询策略
            strategy = self.db.query(Strategy).filter(
                and_(Strategy.id == strategy_id, Strategy.user_id == user_id)
            ).first()
            
            if not strategy:
                return False
            
            # 检查策略状态
            if strategy.status == StrategyStatus.ACTIVE:
                raise ValueError("无法删除活跃状态的策略")
            
            # 删除策略
            self.db.delete(strategy)
            self.db.commit()
            
            # 清除缓存
            self.cache.clear_strategy_cache(str(strategy_id))
            
            logger.info(f"策略删除成功: {strategy_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除策略失败: {e}")
            raise
    
    def list_strategies(self, params: StrategyQueryParams, user_id: Optional[int] = None) -> StrategyListResponse:
        """
        获取策略列表
        
        Args:
            params: 查询参数
            user_id: 用户ID
            
        Returns:
            StrategyListResponse: 策略列表响应
        """
        try:
            # 构建查询
            query = self.db.query(Strategy)
            
            # 用户过滤
            if user_id:
                query = query.filter(Strategy.user_id == user_id)
            elif params.user_id:
                query = query.filter(Strategy.user_id == params.user_id)
            
            # 策略类型过滤
            if params.strategy_type:
                query = query.filter(Strategy.strategy_type == params.strategy_type)
            
            # 状态过滤
            if params.status:
                query = query.filter(Strategy.status == params.status)
            
            # 搜索过滤
            if params.search:
                search_term = f"%{params.search}%"
                query = query.filter(
                    or_(
                        Strategy.name.ilike(search_term),
                        Strategy.description.ilike(search_term)
                    )
                )
            
            # 总数统计
            total = query.count()
            
            # 排序
            if params.sort_by:
                sort_column = getattr(Strategy, params.sort_by, Strategy.created_at)
                if params.sort_order == "asc":
                    query = query.order_by(asc(sort_column))
                else:
                    query = query.order_by(desc(sort_column))
            
            # 分页
            offset = (params.page - 1) * params.size
            strategies = query.offset(offset).limit(params.size).all()
            
            # 转换为响应格式
            strategy_responses = [StrategyResponse.from_orm(s) for s in strategies]
            
            return StrategyListResponse(
                strategies=strategy_responses,
                total=total,
                page=params.page,
                size=params.size
            )
            
        except Exception as e:
            logger.error(f"获取策略列表失败: {e}")
            raise
    
    def start_strategy(self, strategy_id: int, user_id: int) -> bool:
        """
        启动策略
        
        Args:
            strategy_id: 策略ID
            user_id: 用户ID
            
        Returns:
            bool: 是否启动成功
        """
        try:
            strategy = self.db.query(Strategy).filter(
                and_(Strategy.id == strategy_id, Strategy.user_id == user_id)
            ).first()
            
            if not strategy:
                return False
            
            # 检查策略状态
            if strategy.status not in [StrategyStatus.DRAFT, StrategyStatus.PAUSED, StrategyStatus.STOPPED]:
                raise ValueError(f"策略状态 {strategy.status} 无法启动")
            
            # 验证策略配置
            if not self._validate_strategy_config(strategy):
                raise ValueError("策略配置验证失败")
            
            # 更新状态
            strategy.status = StrategyStatus.ACTIVE
            strategy.last_run_at = datetime.utcnow()
            strategy.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # 更新缓存
            self._cache_strategy(strategy)
            
            logger.info(f"策略启动成功: {strategy_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"启动策略失败: {e}")
            raise
    
    def stop_strategy(self, strategy_id: int, user_id: int) -> bool:
        """
        停止策略
        
        Args:
            strategy_id: 策略ID
            user_id: 用户ID
            
        Returns:
            bool: 是否停止成功
        """
        try:
            strategy = self.db.query(Strategy).filter(
                and_(Strategy.id == strategy_id, Strategy.user_id == user_id)
            ).first()
            
            if not strategy:
                return False
            
            # 更新状态
            strategy.status = StrategyStatus.STOPPED
            strategy.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # 更新缓存
            self._cache_strategy(strategy)
            
            logger.info(f"策略停止成功: {strategy_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"停止策略失败: {e}")
            raise
    
    def get_strategy_performance(self, strategy_id: int, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        获取策略性能数据
        
        Args:
            strategy_id: 策略ID
            user_id: 用户ID
            days: 查询天数
            
        Returns:
            Dict[str, Any]: 性能数据
        """
        try:
            strategy = self.db.query(Strategy).filter(
                and_(Strategy.id == strategy_id, Strategy.user_id == user_id)
            ).first()
            
            if not strategy:
                return {}
            
            # 获取性能记录
            start_date = datetime.utcnow() - timedelta(days=days)
            performance_records = self.db.query(PerformanceRecord).filter(
                and_(
                    PerformanceRecord.strategy_id == strategy_id,
                    PerformanceRecord.timestamp >= start_date
                )
            ).order_by(PerformanceRecord.timestamp).all()
            
            # 计算性能指标
            performance_data = self._calculate_performance_metrics(performance_records)
            
            return {
                "strategy_id": strategy_id,
                "strategy_name": strategy.name,
                "period_days": days,
                "performance_metrics": performance_data,
                "records_count": len(performance_records)
            }
            
        except Exception as e:
            logger.error(f"获取策略性能失败: {e}")
            return {}
    
    def _cache_strategy(self, strategy: Strategy):
        """
        缓存策略数据
        
        Args:
            strategy: 策略实例
        """
        try:
            strategy_data = strategy.to_dict()
            self.cache.cache_strategy_data(str(strategy.id), strategy_data)
        except Exception as e:
            logger.warning(f"缓存策略数据失败: {e}")
    
    def _validate_strategy_config(self, strategy: Strategy) -> bool:
        """
        验证策略配置
        
        Args:
            strategy: 策略实例
            
        Returns:
            bool: 是否验证通过
        """
        try:
            # 检查必要字段
            if not strategy.code:
                logger.error("策略代码不能为空")
                return False
            
            if not strategy.symbols:
                logger.error("交易标的不能为空")
                return False
            
            if strategy.initial_capital <= 0:
                logger.error("初始资金必须大于0")
                return False
            
            # 检查风险配置
            if strategy.risk_config:
                max_drawdown = strategy.risk_config.get('max_drawdown', 0.2)
                if max_drawdown <= 0 or max_drawdown > 1:
                    logger.error("最大回撤配置无效")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证策略配置失败: {e}")
            return False
    
    def _calculate_performance_metrics(self, records: List) -> Dict[str, Any]:
        """
        计算性能指标
        
        Args:
            records: 性能记录列表
            
        Returns:
            Dict[str, Any]: 性能指标
        """
        if not records:
            return {}
        
        try:
            # 提取数据
            values = [r.portfolio_value for r in records]
            returns = [r.daily_return for r in records if r.daily_return is not None]
            
            # 计算基本指标
            total_return = (values[-1] - values[0]) / values[0] if len(values) > 1 else 0
            max_value = max(values)
            current_drawdown = (max_value - values[-1]) / max_value if max_value > 0 else 0
            
            # 计算波动率
            volatility = 0
            if len(returns) > 1:
                import statistics
                volatility = statistics.stdev(returns)
            
            # 计算夏普比率
            sharpe_ratio = 0
            if volatility > 0 and returns:
                avg_return = sum(returns) / len(returns)
                sharpe_ratio = avg_return / volatility
            
            return {
                "total_return": total_return,
                "current_drawdown": current_drawdown,
                "volatility": volatility,
                "sharpe_ratio": sharpe_ratio,
                "portfolio_value": values[-1],
                "max_portfolio_value": max_value,
                "records_count": len(records)
            }
            
        except Exception as e:
            logger.error(f"计算性能指标失败: {e}")
            return {}