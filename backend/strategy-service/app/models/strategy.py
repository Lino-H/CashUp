#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略数据模型

定义策略相关的数据库模型，包括策略基本信息、策略参数、
回测结果、性能指标等模型。
"""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

from ..core.database import Base


class StrategyType(str, Enum):
    """策略类型枚举"""
    TECHNICAL = "technical"  # 技术指标策略
    FUNDAMENTAL = "fundamental"  # 基本面策略
    QUANTITATIVE = "quantitative"  # 量化因子策略
    MACHINE_LEARNING = "machine_learning"  # 机器学习策略
    ARBITRAGE = "arbitrage"  # 套利策略
    GRID = "grid"  # 网格策略
    CUSTOM = "custom"  # 自定义策略


class StrategyStatus(str, Enum):
    """策略状态枚举"""
    DRAFT = "draft"  # 草稿
    TESTING = "testing"  # 测试中
    ACTIVE = "active"  # 活跃
    PAUSED = "paused"  # 暂停
    STOPPED = "stopped"  # 停止
    ARCHIVED = "archived"  # 归档


class BacktestStatus(str, Enum):
    """回测状态枚举"""
    PENDING = "pending"  # 等待中
    RUNNING = "running"  # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


class Strategy(Base):
    """
    策略模型
    
    存储策略的基本信息、配置参数、状态等
    """
    __tablename__ = "strategies"
    
    # 基本信息
    id = Column(Integer, primary_key=True, index=True, comment="策略ID")
    name = Column(String(100), nullable=False, comment="策略名称")
    description = Column(Text, comment="策略描述")
    strategy_type = Column(String(20), nullable=False, default=StrategyType.TECHNICAL, comment="策略类型")
    status = Column(String(20), nullable=False, default=StrategyStatus.DRAFT, comment="策略状态")
    
    # 策略代码和配置
    code = Column(Text, comment="策略代码")
    parameters = Column(JSON, comment="策略参数")
    risk_config = Column(JSON, comment="风险配置")
    
    # 交易配置
    symbols = Column(JSON, comment="交易标的")
    timeframe = Column(String(10), comment="时间周期")
    initial_capital = Column(Float, default=10000.0, comment="初始资金")
    max_positions = Column(Integer, default=5, comment="最大持仓数")
    
    # 用户信息
    user_id = Column(Integer, nullable=False, comment="创建用户ID")
    
    # 统计信息
    total_trades = Column(Integer, default=0, comment="总交易次数")
    win_rate = Column(Float, default=0.0, comment="胜率")
    total_return = Column(Float, default=0.0, comment="总收益率")
    max_drawdown = Column(Float, default=0.0, comment="最大回撤")
    sharpe_ratio = Column(Float, default=0.0, comment="夏普比率")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    last_run_at = Column(DateTime, comment="最后运行时间")
    
    # 关系
    backtests = relationship("Backtest", back_populates="strategy", cascade="all, delete-orphan")
    performance_records = relationship("PerformanceRecord", back_populates="strategy", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_strategy_user_status', 'user_id', 'status'),
        Index('idx_strategy_type', 'strategy_type'),
        Index('idx_strategy_created', 'created_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "strategy_type": self.strategy_type,
            "status": self.status,
            "parameters": self.parameters,
            "risk_config": self.risk_config,
            "symbols": self.symbols,
            "timeframe": self.timeframe,
            "initial_capital": self.initial_capital,
            "max_positions": self.max_positions,
            "user_id": self.user_id,
            "total_trades": self.total_trades,
            "win_rate": self.win_rate,
            "total_return": self.total_return,
            "max_drawdown": self.max_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None
        }


class Backtest(Base):
    """
    回测模型
    
    存储策略回测的配置、结果和性能指标
    """
    __tablename__ = "backtests"
    
    # 基本信息
    id = Column(Integer, primary_key=True, index=True, comment="回测ID")
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, comment="策略ID")
    name = Column(String(100), nullable=False, comment="回测名称")
    description = Column(Text, comment="回测描述")
    status = Column(String(20), nullable=False, default=BacktestStatus.PENDING, comment="回测状态")
    
    # 回测配置
    start_date = Column(DateTime, nullable=False, comment="开始日期")
    end_date = Column(DateTime, nullable=False, comment="结束日期")
    initial_capital = Column(Float, nullable=False, comment="初始资金")
    commission = Column(Float, default=0.001, comment="手续费率")
    slippage = Column(Float, default=0.0001, comment="滑点")
    
    # 回测结果
    final_capital = Column(Float, comment="最终资金")
    total_return = Column(Float, comment="总收益率")
    annual_return = Column(Float, comment="年化收益率")
    max_drawdown = Column(Float, comment="最大回撤")
    sharpe_ratio = Column(Float, comment="夏普比率")
    sortino_ratio = Column(Float, comment="索提诺比率")
    calmar_ratio = Column(Float, comment="卡玛比率")
    
    # 交易统计
    total_trades = Column(Integer, default=0, comment="总交易次数")
    winning_trades = Column(Integer, default=0, comment="盈利交易次数")
    losing_trades = Column(Integer, default=0, comment="亏损交易次数")
    win_rate = Column(Float, default=0.0, comment="胜率")
    avg_win = Column(Float, default=0.0, comment="平均盈利")
    avg_loss = Column(Float, default=0.0, comment="平均亏损")
    profit_factor = Column(Float, default=0.0, comment="盈亏比")
    
    # 详细数据
    trades_data = Column(JSON, comment="交易明细数据")
    equity_curve = Column(JSON, comment="资金曲线数据")
    performance_metrics = Column(JSON, comment="性能指标详情")
    
    # 执行信息
    execution_time = Column(Float, comment="执行时间（秒）")
    error_message = Column(Text, comment="错误信息")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    started_at = Column(DateTime, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    
    # 关系
    strategy = relationship("Strategy", back_populates="backtests")
    
    # 索引
    __table_args__ = (
        Index('idx_backtest_strategy', 'strategy_id'),
        Index('idx_backtest_status', 'status'),
        Index('idx_backtest_created', 'created_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "strategy_id": self.strategy_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "initial_capital": self.initial_capital,
            "commission": self.commission,
            "slippage": self.slippage,
            "final_capital": self.final_capital,
            "total_return": self.total_return,
            "annual_return": self.annual_return,
            "max_drawdown": self.max_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "calmar_ratio": self.calmar_ratio,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": self.win_rate,
            "avg_win": self.avg_win,
            "avg_loss": self.avg_loss,
            "profit_factor": self.profit_factor,
            "execution_time": self.execution_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class PerformanceRecord(Base):
    """
    性能记录模型
    
    存储策略的实时性能数据和历史记录
    """
    __tablename__ = "performance_records"
    
    # 基本信息
    id = Column(Integer, primary_key=True, index=True, comment="记录ID")
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, comment="策略ID")
    
    # 性能数据
    timestamp = Column(DateTime, nullable=False, comment="记录时间")
    portfolio_value = Column(Float, nullable=False, comment="组合价值")
    cash = Column(Float, nullable=False, comment="现金")
    positions_value = Column(Float, nullable=False, comment="持仓价值")
    
    # 收益指标
    daily_return = Column(Float, comment="日收益率")
    cumulative_return = Column(Float, comment="累计收益率")
    drawdown = Column(Float, comment="回撤")
    
    # 风险指标
    volatility = Column(Float, comment="波动率")
    beta = Column(Float, comment="贝塔值")
    alpha = Column(Float, comment="阿尔法值")
    
    # 持仓信息
    positions = Column(JSON, comment="持仓详情")
    
    # 关系
    strategy = relationship("Strategy", back_populates="performance_records")
    
    # 索引
    __table_args__ = (
        Index('idx_performance_strategy_time', 'strategy_id', 'timestamp'),
        Index('idx_performance_timestamp', 'timestamp'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "strategy_id": self.strategy_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "portfolio_value": self.portfolio_value,
            "cash": self.cash,
            "positions_value": self.positions_value,
            "daily_return": self.daily_return,
            "cumulative_return": self.cumulative_return,
            "drawdown": self.drawdown,
            "volatility": self.volatility,
            "beta": self.beta,
            "alpha": self.alpha,
            "positions": self.positions
        }


class StrategyTemplate(Base):
    """
    策略模板模型
    
    存储预定义的策略模板，用户可以基于模板创建策略
    """
    __tablename__ = "strategy_templates"
    
    # 基本信息
    id = Column(Integer, primary_key=True, index=True, comment="模板ID")
    name = Column(String(100), nullable=False, comment="模板名称")
    description = Column(Text, comment="模板描述")
    category = Column(String(50), comment="模板分类")
    strategy_type = Column(String(20), nullable=False, comment="策略类型")
    
    # 模板内容
    code_template = Column(Text, nullable=False, comment="代码模板")
    default_parameters = Column(JSON, comment="默认参数")
    parameter_schema = Column(JSON, comment="参数结构")
    
    # 模板信息
    author = Column(String(100), comment="作者")
    version = Column(String(20), default="1.0.0", comment="版本")
    tags = Column(JSON, comment="标签")
    
    # 使用统计
    usage_count = Column(Integer, default=0, comment="使用次数")
    rating = Column(Float, default=0.0, comment="评分")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_public = Column(Boolean, default=False, comment="是否公开")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 索引
    __table_args__ = (
        Index('idx_template_category', 'category'),
        Index('idx_template_type', 'strategy_type'),
        Index('idx_template_active', 'is_active'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "strategy_type": self.strategy_type,
            "default_parameters": self.default_parameters,
            "parameter_schema": self.parameter_schema,
            "author": self.author,
            "version": self.version,
            "tags": self.tags,
            "usage_count": self.usage_count,
            "rating": self.rating,
            "is_active": self.is_active,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }