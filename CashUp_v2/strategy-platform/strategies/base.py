"""
策略基类和接口定义
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import pandas as pd

class SignalType(Enum):
    """信号类型"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE = "close"

class OrderType(Enum):
    """订单类型"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    ICEBERG = "iceberg"

class TimeFrame(Enum):
    """时间周期"""
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    THIRTY_MINUTES = "30m"
    ONE_HOUR = "1h"
    FOUR_HOURS = "4h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"

class StrategySignal:
    """策略信号"""
    
    def __init__(
        self,
        signal_type: SignalType,
        symbol: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        order_type: OrderType = OrderType.MARKET,
        reason: str = "",
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.signal_type = signal_type
        self.symbol = symbol
        self.quantity = quantity
        self.price = price
        self.stop_price = stop_price
        self.order_type = order_type
        self.reason = reason
        self.confidence = confidence
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

class StrategyConfig:
    """策略配置"""
    
    def __init__(
        self,
        symbols: List[str],
        timeframe: TimeFrame,
        initial_capital: float = 10000.0,
        max_position_size: float = 1.0,
        risk_per_trade: float = 0.02,
        max_drawdown: float = 0.2,
        stop_loss: float = 0.05,
        take_profit: float = 0.1,
        commission: float = 0.001,
        slippage: float = 0.0005,
        **kwargs
    ):
        self.symbols = symbols
        self.timeframe = timeframe
        self.initial_capital = initial_capital
        self.max_position_size = max_position_size
        self.risk_per_trade = risk_per_trade
        self.max_drawdown = max_drawdown
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.commission = commission
        self.slippage = slippage
        self.extra_params = kwargs

class BacktestResult:
    """回测结果"""
    
    def __init__(self):
        self.total_return: float = 0.0
        self.sharpe_ratio: float = 0.0
        self.max_drawdown: float = 0.0
        self.win_rate: float = 0.0
        self.profit_factor: float = 0.0
        self.total_trades: int = 0
        self.profitable_trades: int = 0
        self.avg_win: float = 0.0
        self.avg_loss: float = 0.0
        self.final_capital: float = 0.0
        self.equity_curve: List[float] = []
        self.drawdown_curve: List[float] = []
        self.trades: List[Dict[str, Any]] = []

class StrategyBase(ABC):
    """策略基类"""
    
    def __init__(self, config: StrategyConfig):
        self.config = config
        self.name = self.__class__.__name__
        self.version = "1.0.0"
        self.description = self.__doc__ or ""
        self.author = ""
        self.is_initialized = False
        self.position = {}  # 当前持仓
        self.cash = config.initial_capital
        self.equity = config.initial_capital
        self.trades = []
        self.equity_history = []
        self.drawdown_history = []
        
    @abstractmethod
    def initialize(self) -> None:
        """策略初始化"""
        pass
    
    @abstractmethod
    def on_data(self, data: pd.DataFrame) -> Optional[StrategySignal]:
        """
        处理市场数据，返回交易信号
        
        Args:
            data: 市场数据，包含OHLCV等信息
            
        Returns:
            交易信号，如果没有信号则返回None
        """
        pass
    
    @abstractmethod
    def on_order_filled(self, order: Dict[str, Any]) -> None:
        """订单成交回调"""
        pass
    
    @abstractmethod
    def on_error(self, error: Exception) -> None:
        """错误处理回调"""
        pass
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标
        
        Args:
            data: 原始市场数据
            
        Returns:
            包含技术指标的数据
        """
        return data
    
    def risk_management(self, signal: StrategySignal) -> bool:
        """
        风险管理
        
        Args:
            signal: 交易信号
            
        Returns:
            是否允许交易
        """
        # 计算当前回撤
        if len(self.equity_history) > 0:
            peak_equity = max(self.equity_history)
            current_drawdown = (peak_equity - self.equity) / peak_equity
            
            # 检查最大回撤限制
            if current_drawdown > self.config.max_drawdown:
                return False
        
        # 计算仓位风险
        position_value = abs(signal.quantity * signal.price if signal.price else 0)
        risk_amount = position_value * self.config.risk_per_trade
        
        if risk_amount > self.equity * self.config.risk_per_trade:
            return False
        
        return True
    
    def calculate_position_size(self, signal: StrategySignal) -> float:
        """
        计算仓位大小
        
        Args:
            signal: 交易信号
            
        Returns:
            建议仓位大小
        """
        if signal.signal_type == SignalType.HOLD:
            return 0
        
        # 基于风险的仓位计算
        risk_amount = self.equity * self.config.risk_per_trade
        
        if signal.stop_price:
            # 基于止损的仓位计算
            price = signal.price or self.get_current_price(signal.symbol)
            stop_loss_percent = abs(price - signal.stop_price) / price
            position_size = risk_amount / stop_loss_percent
        else:
            # 固定风险百分比
            position_size = risk_amount / (self.equity * self.config.stop_loss)
        
        # 限制最大仓位
        max_position = self.equity * self.config.max_position_size
        position_size = min(position_size, max_position)
        
        return position_size
    
    def get_current_price(self, symbol: str) -> float:
        """获取当前价格"""
        # 在实际实现中，这里应该从数据源获取最新价格
        return 0.0
    
    def update_equity(self, price: float, symbol: str) -> None:
        """更新权益"""
        # 计算当前持仓价值
        position_value = 0.0
        if symbol in self.position:
            position_value = self.position[symbol] * price
        
        # 更新权益
        self.equity = self.cash + position_value
        self.equity_history.append(self.equity)
    
    def calculate_metrics(self) -> BacktestResult:
        """计算策略性能指标"""
        if not self.trades:
            return BacktestResult()
        
        # 计算基本指标
        profitable_trades = [t for t in self.trades if t['pnl'] > 0]
        losing_trades = [t for t in self.trades if t['pnl'] < 0]
        
        total_trades = len(self.trades)
        win_rate = len(profitable_trades) / total_trades if total_trades > 0 else 0
        
        avg_win = sum(t['pnl'] for t in profitable_trades) / len(profitable_trades) if profitable_trades else 0
        avg_loss = sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        profit_factor = abs(sum(t['pnl'] for t in profitable_trades) / sum(t['pnl'] for t in losing_trades)) if losing_trades else 0
        
        # 计算总收益率
        total_return = (self.equity - self.config.initial_capital) / self.config.initial_capital
        
        # 计算夏普比率（简化版）
        if len(self.equity_history) > 1:
            returns = []
            for i in range(1, len(self.equity_history)):
                ret = (self.equity_history[i] - self.equity_history[i-1]) / self.equity_history[i-1]
                returns.append(ret)
            
            if returns:
                avg_return = sum(returns) / len(returns)
                return_std = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
                sharpe_ratio = avg_return / return_std if return_std > 0 else 0
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        # 计算最大回撤
        if self.equity_history:
            peak_equity = self.equity_history[0]
            max_drawdown = 0
            
            for equity in self.equity_history:
                if equity > peak_equity:
                    peak_equity = equity
                else:
                    drawdown = (peak_equity - equity) / peak_equity
                    max_drawdown = max(max_drawdown, drawdown)
        else:
            max_drawdown = 0
        
        result = BacktestResult()
        result.total_return = total_return
        result.sharpe_ratio = sharpe_ratio
        result.max_drawdown = max_drawdown
        result.win_rate = win_rate
        result.profit_factor = profit_factor
        result.total_trades = total_trades
        result.profitable_trades = len(profitable_trades)
        result.avg_win = avg_win
        result.avg_loss = avg_loss
        result.final_capital = self.equity
        result.equity_curve = self.equity_history
        result.drawdown_curve = self.drawdown_history
        result.trades = self.trades
        
        return result
    
    def get_info(self) -> Dict[str, Any]:
        """获取策略信息"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "config": self.config.__dict__,
            "performance": self.calculate_metrics().__dict__
        }