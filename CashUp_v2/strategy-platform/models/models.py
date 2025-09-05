"""
数据库模型定义
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from .connection import Base

class Strategy(Base):
    """策略表"""
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    type = Column(String(50), nullable=False, default="basic")
    code = Column(Text, nullable=False)
    config = Column(JSON, default={})
    version = Column(String(20), default="1.0.0")
    author = Column(String(100), default="")
    tags = Column(JSON, default=[])
    status = Column(String(20), default="draft")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_run_at = Column(DateTime)
    performance = Column(JSON, default={})
    error_message = Column(Text)
    
    # 关系
    backtests = relationship("Backtest", back_populates="strategy")

class Backtest(Base):
    """回测表"""
    __tablename__ = "backtests"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    config = Column(JSON, nullable=False)
    status = Column(String(20), default="pending")
    start_time = Column(DateTime, default=func.now())
    end_time = Column(DateTime)
    result = Column(JSON)
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    strategy = relationship("Strategy", back_populates="backtests")

class DataCache(Base):
    """数据缓存表"""
    __tablename__ = "data_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(500), nullable=False, unique=True, index=True)
    data = Column(JSON, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    ttl = Column(Integer, default=300)  # 缓存时间（秒）
    
    # 索引
    __table_args__ = (
        {'extend_existing': True}
    )

class StrategyLog(Base):
    """策略日志表"""
    __tablename__ = "strategy_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    level = Column(String(20), default="INFO")
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    metadata = Column(JSON, default={})
    
    # 关系
    strategy = relationship("Strategy")

class StrategyPerformance(Base):
    """策略性能表"""
    __tablename__ = "strategy_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    total_return = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)
    total_trades = Column(Integer, default=0)
    profitable_trades = Column(Integer, default=0)
    final_capital = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())
    
    # 关系
    strategy = relationship("Strategy")
    
    # 复合索引
    __table_args__ = (
        {'extend_existing': True}
    )

class StrategyTemplate(Base):
    """策略模板表"""
    __tablename__ = "strategy_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    description = Column(Text)
    template_code = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class MarketData(Base):
    """市场数据表"""
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())
    
    # 复合索引
    __table_args__ = (
        {'extend_existing': True}
    )

class DataSource(Base):
    """数据源表"""
    __tablename__ = "data_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    type = Column(String(50), nullable=False)
    url = Column(String(500), nullable=False)
    api_key = Column(String(500))
    is_active = Column(Boolean, default=True)
    rate_limit = Column(Integer, default=1000)
    last_used = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class StrategyExecution(Base):
    """策略执行表"""
    __tablename__ = "strategy_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    execution_id = Column(String(100), nullable=False, unique=True)
    status = Column(String(20), default="running")
    start_time = Column(DateTime, default=func.now())
    end_time = Column(DateTime)
    signals_generated = Column(Integer, default=0)
    trades_executed = Column(Integer, default=0)
    error_message = Column(Text)
    performance_data = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    
    # 关系
    strategy = relationship("Strategy")

class StrategySignal(Base):
    """策略信号表"""
    __tablename__ = "strategy_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    execution_id = Column(String(100), nullable=False)
    symbol = Column(String(20), nullable=False)
    signal_type = Column(String(20), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float)
    confidence = Column(Float, default=1.0)
    reason = Column(Text)
    metadata = Column(JSON, default={})
    timestamp = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    
    # 关系
    strategy = relationship("Strategy")

class StrategyConfigHistory(Base):
    """策略配置历史表"""
    __tablename__ = "strategy_config_history"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    config = Column(JSON, nullable=False)
    changed_by = Column(String(100))
    change_reason = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    # 关系
    strategy = relationship("Strategy")