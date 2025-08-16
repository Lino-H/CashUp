#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略数据模式

定义策略相关的Pydantic模型，用于API请求和响应的数据验证、
序列化和文档生成。
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class StrategyType(str, Enum):
    """策略类型枚举"""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    QUANTITATIVE = "quantitative"
    MACHINE_LEARNING = "machine_learning"
    ARBITRAGE = "arbitrage"
    GRID = "grid"
    CUSTOM = "custom"


class StrategyStatus(str, Enum):
    """策略状态枚举"""
    DRAFT = "draft"
    TESTING = "testing"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    ARCHIVED = "archived"


class BacktestStatus(str, Enum):
    """回测状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# 策略相关模式
class StrategyBase(BaseModel):
    """策略基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="策略名称")
    description: Optional[str] = Field(None, description="策略描述")
    strategy_type: StrategyType = Field(StrategyType.TECHNICAL, description="策略类型")
    symbols: Optional[List[str]] = Field(None, description="交易标的")
    timeframe: Optional[str] = Field("1h", description="时间周期")
    initial_capital: float = Field(10000.0, gt=0, description="初始资金")
    max_positions: int = Field(5, ge=1, le=20, description="最大持仓数")
    
    @validator('symbols')
    def validate_symbols(cls, v):
        """验证交易标的"""
        if v and len(v) == 0:
            raise ValueError('交易标的不能为空列表')
        return v


class StrategyCreate(StrategyBase):
    """创建策略模式"""
    code: Optional[str] = Field(None, description="策略代码")
    parameters: Optional[Dict[str, Any]] = Field(None, description="策略参数")
    risk_config: Optional[Dict[str, Any]] = Field(None, description="风险配置")
    
    @validator('parameters')
    def validate_parameters(cls, v):
        """验证策略参数"""
        if v is not None and not isinstance(v, dict):
            raise ValueError('策略参数必须是字典格式')
        return v


class StrategyUpdate(BaseModel):
    """更新策略模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="策略名称")
    description: Optional[str] = Field(None, description="策略描述")
    status: Optional[StrategyStatus] = Field(None, description="策略状态")
    code: Optional[str] = Field(None, description="策略代码")
    parameters: Optional[Dict[str, Any]] = Field(None, description="策略参数")
    risk_config: Optional[Dict[str, Any]] = Field(None, description="风险配置")
    symbols: Optional[List[str]] = Field(None, description="交易标的")
    timeframe: Optional[str] = Field(None, description="时间周期")
    initial_capital: Optional[float] = Field(None, gt=0, description="初始资金")
    max_positions: Optional[int] = Field(None, ge=1, le=20, description="最大持仓数")


class StrategyResponse(StrategyBase):
    """策略响应模式"""
    id: int = Field(..., description="策略ID")
    status: StrategyStatus = Field(..., description="策略状态")
    user_id: int = Field(..., description="创建用户ID")
    code: Optional[str] = Field(None, description="策略代码")
    parameters: Optional[Dict[str, Any]] = Field(None, description="策略参数")
    risk_config: Optional[Dict[str, Any]] = Field(None, description="风险配置")
    
    # 统计信息
    total_trades: int = Field(0, description="总交易次数")
    win_rate: float = Field(0.0, description="胜率")
    total_return: float = Field(0.0, description="总收益率")
    max_drawdown: float = Field(0.0, description="最大回撤")
    sharpe_ratio: float = Field(0.0, description="夏普比率")
    
    # 时间戳
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_run_at: Optional[datetime] = Field(None, description="最后运行时间")
    
    class Config:
        from_attributes = True


class StrategyListResponse(BaseModel):
    """策略列表响应模式"""
    strategies: List[StrategyResponse] = Field(..., description="策略列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")


class StrategyDetailResponse(StrategyResponse):
    """策略详情响应模式"""
    code: Optional[str] = Field(None, description="策略代码")
    backtests: Optional[List[Dict[str, Any]]] = Field(None, description="回测历史")
    performance_records: Optional[List[Dict[str, Any]]] = Field(None, description="性能记录")


# 回测相关模式
class BacktestBase(BaseModel):
    """回测基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="回测名称")
    description: Optional[str] = Field(None, description="回测描述")
    start_date: datetime = Field(..., description="开始日期")
    end_date: datetime = Field(..., description="结束日期")
    initial_capital: float = Field(10000.0, gt=0, description="初始资金")
    commission: float = Field(0.001, ge=0, le=0.1, description="手续费率")
    slippage: float = Field(0.0001, ge=0, le=0.01, description="滑点")
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        """验证日期范围"""
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('结束日期必须大于开始日期')
        return v


class BacktestCreate(BacktestBase):
    """创建回测模式"""
    strategy_id: int = Field(..., description="策略ID")


class BacktestResponse(BacktestBase):
    """回测响应模式"""
    id: int = Field(..., description="回测ID")
    strategy_id: int = Field(..., description="策略ID")
    status: BacktestStatus = Field(..., description="回测状态")
    
    # 回测结果
    final_capital: Optional[float] = Field(None, description="最终资金")
    total_return: Optional[float] = Field(None, description="总收益率")
    annual_return: Optional[float] = Field(None, description="年化收益率")
    max_drawdown: Optional[float] = Field(None, description="最大回撤")
    sharpe_ratio: Optional[float] = Field(None, description="夏普比率")
    sortino_ratio: Optional[float] = Field(None, description="索提诺比率")
    calmar_ratio: Optional[float] = Field(None, description="卡玛比率")
    
    # 交易统计
    total_trades: int = Field(0, description="总交易次数")
    winning_trades: int = Field(0, description="盈利交易次数")
    losing_trades: int = Field(0, description="亏损交易次数")
    win_rate: float = Field(0.0, description="胜率")
    avg_win: float = Field(0.0, description="平均盈利")
    avg_loss: float = Field(0.0, description="平均亏损")
    profit_factor: float = Field(0.0, description="盈亏比")
    
    # 执行信息
    execution_time: Optional[float] = Field(None, description="执行时间（秒）")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    # 时间戳
    created_at: datetime = Field(..., description="创建时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    
    class Config:
        from_attributes = True


class BacktestDetailResponse(BacktestResponse):
    """回测详情响应模式"""
    trades_data: Optional[List[Dict[str, Any]]] = Field(None, description="交易明细数据")
    equity_curve: Optional[List[Dict[str, Any]]] = Field(None, description="资金曲线数据")
    performance_metrics: Optional[Dict[str, Any]] = Field(None, description="性能指标详情")


class BacktestListResponse(BaseModel):
    """回测列表响应模式"""
    backtests: List[BacktestResponse] = Field(..., description="回测列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")


# 性能记录相关模式
class PerformanceRecordResponse(BaseModel):
    """性能记录响应模式"""
    id: int = Field(..., description="记录ID")
    strategy_id: int = Field(..., description="策略ID")
    timestamp: datetime = Field(..., description="记录时间")
    portfolio_value: float = Field(..., description="组合价值")
    cash: float = Field(..., description="现金")
    positions_value: float = Field(..., description="持仓价值")
    daily_return: Optional[float] = Field(None, description="日收益率")
    cumulative_return: Optional[float] = Field(None, description="累计收益率")
    drawdown: Optional[float] = Field(None, description="回撤")
    volatility: Optional[float] = Field(None, description="波动率")
    beta: Optional[float] = Field(None, description="贝塔值")
    alpha: Optional[float] = Field(None, description="阿尔法值")
    positions: Optional[Dict[str, Any]] = Field(None, description="持仓详情")
    
    class Config:
        from_attributes = True


# 策略模板相关模式
class StrategyTemplateBase(BaseModel):
    """策略模板基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    category: Optional[str] = Field(None, description="模板分类")
    strategy_type: StrategyType = Field(..., description="策略类型")
    author: Optional[str] = Field(None, description="作者")
    version: str = Field("1.0.0", description="版本")
    tags: Optional[List[str]] = Field(None, description="标签")


class StrategyTemplateCreate(StrategyTemplateBase):
    """创建策略模板模式"""
    code_template: str = Field(..., description="代码模板")
    default_parameters: Optional[Dict[str, Any]] = Field(None, description="默认参数")
    parameter_schema: Optional[Dict[str, Any]] = Field(None, description="参数结构")
    is_public: bool = Field(False, description="是否公开")


class StrategyTemplateResponse(StrategyTemplateBase):
    """策略模板响应模式"""
    id: int = Field(..., description="模板ID")
    code_template: str = Field(..., description="代码模板")
    default_parameters: Optional[Dict[str, Any]] = Field(None, description="默认参数")
    parameter_schema: Optional[Dict[str, Any]] = Field(None, description="参数结构")
    usage_count: int = Field(0, description="使用次数")
    rating: float = Field(0.0, description="评分")
    is_active: bool = Field(True, description="是否激活")
    is_public: bool = Field(False, description="是否公开")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


# 通用响应模式
class MessageResponse(BaseModel):
    """消息响应模式"""
    message: str = Field(..., description="响应消息")
    success: bool = Field(True, description="是否成功")
    data: Optional[Dict[str, Any]] = Field(None, description="附加数据")


class ErrorResponse(BaseModel):
    """错误响应模式"""
    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="错误详情")
    code: Optional[str] = Field(None, description="错误代码")


# 分页查询参数
class PaginationParams(BaseModel):
    """分页参数模式"""
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页大小")
    sort_by: Optional[str] = Field("created_at", description="排序字段")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$", description="排序方向")


# 策略查询参数
class StrategyQueryParams(PaginationParams):
    """策略查询参数模式"""
    strategy_type: Optional[StrategyType] = Field(None, description="策略类型")
    status: Optional[StrategyStatus] = Field(None, description="策略状态")
    search: Optional[str] = Field(None, description="搜索关键词")
    user_id: Optional[int] = Field(None, description="用户ID")


# 回测查询参数
class BacktestQueryParams(PaginationParams):
    """回测查询参数模式"""
    strategy_id: Optional[int] = Field(None, description="策略ID")
    status: Optional[BacktestStatus] = Field(None, description="回测状态")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")