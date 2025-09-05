"""
策略数据模型定义
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class StrategyType(str, Enum):
    """策略类型枚举"""
    BASIC = "basic"
    MA_CROSS = "ma_cross"
    RSI = "rsi"
    GRID = "grid"
    CUSTOM = "custom"

class StrategyStatus(str, Enum):
    """策略状态枚举"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"

class StrategyBase(BaseModel):
    """策略基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="策略名称")
    description: Optional[str] = Field(None, description="策略描述")
    type: StrategyType = Field(StrategyType.BASIC, description="策略类型")
    code: str = Field(..., min_length=1, description="策略代码")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="策略配置")
    version: str = Field("1.0.0", description="策略版本")
    author: str = Field("", description="策略作者")
    tags: List[str] = Field(default_factory=list, description="策略标签")
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('策略名称不能为空')
        return v.strip()

class StrategyCreate(StrategyBase):
    """创建策略模型"""
    pass

class StrategyUpdate(BaseModel):
    """更新策略模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="策略名称")
    description: Optional[str] = Field(None, description="策略描述")
    code: Optional[str] = Field(None, min_length=1, description="策略代码")
    config: Optional[Dict[str, Any]] = Field(None, description="策略配置")
    version: Optional[str] = Field(None, description="策略版本")
    author: Optional[str] = Field(None, description="策略作者")
    tags: Optional[List[str]] = Field(None, description="策略标签")
    status: Optional[StrategyStatus] = Field(None, description="策略状态")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('策略名称不能为空')
            return v.strip()
        return v

class StrategyResponse(StrategyBase):
    """策略响应模型"""
    id: int
    status: StrategyStatus
    created_at: datetime
    updated_at: datetime
    last_run_at: Optional[datetime] = None
    performance: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class StrategyListResponse(BaseModel):
    """策略列表响应模型"""
    strategies: List[StrategyResponse]
    total: int
    skip: int
    limit: int

class StrategyTemplateRequest(BaseModel):
    """策略模板请求模型"""
    strategy_name: str = Field(..., min_length=1, max_length=100, description="策略名称")
    strategy_type: StrategyType = Field(StrategyType.BASIC, description="策略类型")

class StrategyTemplateResponse(BaseModel):
    """策略模板响应模型"""
    template_code: str
    strategy_name: str
    strategy_type: StrategyType
    description: str

class BacktestConfig(BaseModel):
    """回测配置模型"""
    strategy_id: int = Field(..., description="策略ID")
    symbols: List[str] = Field(..., min_items=1, description="交易对列表")
    timeframe: str = Field("1h", description="时间周期")
    start_date: datetime = Field(..., description="开始时间")
    end_date: datetime = Field(..., description="结束时间")
    initial_capital: float = Field(10000.0, gt=0, description="初始资金")
    commission: float = Field(0.001, ge=0, description="手续费率")
    slippage: float = Field(0.0005, ge=0, description="滑点率")
    max_position_size: float = Field(1.0, gt=0, le=1, description="最大仓位大小")
    risk_per_trade: float = Field(0.02, gt=0, le=1, description="每笔交易风险")
    stop_loss: float = Field(0.05, gt=0, le=1, description="止损比例")
    take_profit: float = Field(0.1, gt=0, le=1, description="止盈比例")
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('结束时间必须大于开始时间')
        return v

class BacktestResponse(BaseModel):
    """回测响应模型"""
    backtest_id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    config: BacktestConfig
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class PerformanceMetrics(BaseModel):
    """性能指标模型"""
    total_return: float = Field(description="总收益率")
    annualized_return: float = Field(description="年化收益率")
    volatility: float = Field(description="波动率")
    sharpe_ratio: float = Field(description="夏普比率")
    max_drawdown: float = Field(description="最大回撤")
    calmar_ratio: float = Field(description="卡尔马比率")
    win_rate: float = Field(description="胜率")
    profit_factor: float = Field(description="盈利因子")
    total_trades: int = Field(description="总交易次数")
    profitable_trades: int = Field(description="盈利交易次数")
    avg_win: float = Field(description="平均盈利")
    avg_loss: float = Field(description="平均亏损")
    final_capital: float = Field(description="最终资金")

class DataRequest(BaseModel):
    """数据请求模型"""
    symbols: List[str] = Field(..., min_items=1, description="交易对列表")
    timeframe: str = Field("1h", description="时间周期")
    start_date: Optional[datetime] = Field(None, description="开始时间")
    end_date: Optional[datetime] = Field(None, description="结束时间")
    limit: int = Field(1000, gt=0, le=10000, description="数据条数限制")

class DataResponse(BaseModel):
    """数据响应模型"""
    symbol: str
    timeframe: str
    data: List[Dict[str, Any]]
    count: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class AvailableSymbol(BaseModel):
    """可用交易对模型"""
    symbol: str
    name: str
    base_asset: str
    quote_asset: str
    min_price: float
    max_price: float
    tick_size: float
    step_size: float

class AvailableTimeframe(BaseModel):
    """可用时间周期模型"""
    timeframe: str
    description: str
    interval_seconds: int