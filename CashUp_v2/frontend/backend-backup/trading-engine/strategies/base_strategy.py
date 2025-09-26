"""
策略基类和策略管理器
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
import uuid

from exchanges.base import Ticker, Order, Position, OrderRequest, OrderSide, OrderType, OrderStatus

logger = logging.getLogger(__name__)

@dataclass
class Signal:
    """交易信号"""
    symbol: str
    side: OrderSide
    action: str  # 'buy', 'sell', 'close', 'hold'
    strength: float  # 信号强度 0-1
    price: Optional[float] = None
    quantity: Optional[float] = None
    reason: str = ""
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class Position:
    """策略持仓"""
    symbol: str
    side: OrderSide
    size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    created_at: datetime
    updated_at: datetime

class BaseStrategy(ABC):
    """策略基类"""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.is_running = False
        self.positions: Dict[str, Position] = {}
        self.signals: List[Signal] = []
        self.performance_metrics: Dict[str, Any] = {}

        # 策略参数
        self.max_position_size = config.get('max_position_size', 10.0)
        self.max_drawdown = config.get('max_drawdown', 0.2)
        self.stop_loss_rate = config.get('stop_loss_rate', 0.05)
        self.take_profit_rate = config.get('take_profit_rate', 0.1)
        self.position_risk_percent = config.get('position_risk_percent', 2.0)

    @abstractmethod
    async def analyze_market(self, market_data: Dict[str, Any]) -> List[Signal]:
        """分析市场数据，产生交易信号"""
        pass

    @abstractmethod
    async def on_order_filled(self, order: Order):
        """订单成交回调"""
        pass

    @abstractmethod
    async def on_market_update(self, market_data: Dict[str, Any]):
        """市场数据更新回调"""
        pass

    async def initialize(self):
        """策略初始化"""
        logger.info(f"🚀 策略 {self.name} 初始化...")
        self.is_running = True
        self.performance_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'start_time': datetime.now(),
            'last_update': datetime.now()
        }

    async def stop(self):
        """停止策略"""
        logger.info(f"🛑 策略 {self.name} 停止")
        self.is_running = False

    def add_signal(self, signal: Signal):
        """添加交易信号"""
        self.signals.append(signal)
        logger.info(f"📊 策略 {self.name} 生成信号: {signal.symbol} {signal.action} 强度={signal.strength:.2f}")

    def get_signals(self, limit: int = 10) -> List[Signal]:
        """获取最近的信号"""
        return self.signals[-limit:]

    def update_position(self, symbol: str, side: OrderSide, size: float, price: float):
        """更新持仓"""
        current_time = datetime.now()

        if symbol in self.positions:
            position = self.positions[symbol]
            position.size = size
            position.current_price = price
            position.updated_at = current_time
        else:
            self.positions[symbol] = Position(
                symbol=symbol,
                side=side,
                size=size,
                entry_price=price,
                current_price=price,
                unrealized_pnl=0.0,
                created_at=current_time,
                updated_at=current_time
            )

    def calculate_position_pnl(self, symbol: str, current_price: float) -> float:
        """计算持仓盈亏"""
        if symbol not in self.positions:
            return 0.0

        position = self.positions[symbol]
        if position.side == OrderSide.BUY:
            return (current_price - position.entry_price) * position.size
        else:
            return (position.entry_price - current_price) * position.size

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return self.performance_metrics.copy()

    def should_reduce_position(self, symbol: str, current_price: float) -> bool:
        """是否应该减仓"""
        if symbol not in self.positions:
            return False

        position = self.positions[symbol]
        pnl_ratio = (current_price - position.entry_price) / position.entry_price

        # 止损检查
        if position.side == OrderSide.BUY and pnl_ratio <= -self.stop_loss_rate:
            return True
        elif position.side == OrderSide.SELL and pnl_ratio >= self.stop_loss_rate:
            return True

        # 止盈检查
        if abs(pnl_ratio) >= self.take_profit_rate:
            return True

        return False

class GridStrategy(BaseStrategy):
    """网格交易策略"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("网格策略", config)
        self.grid_levels = config.get('grid_levels', 5)
        self.grid_spacing = config.get('grid_spacing', 0.02)  # 2%间距
        self.base_price = config.get('base_price', 3000.0)
        self.grid_orders = {}  # 管理网格订单

    async def analyze_market(self, market_data: Dict[str, Any]) -> List[Signal]:
        """分析市场并生成网格信号"""
        signals = []
        symbol = list(market_data.keys())[0]  # 假设只有一个交易对
        current_price = market_data[symbol]['last_price']

        # 创建网格订单
        await self._create_grid_orders(symbol, current_price)

        # 检查价格触发的网格
        signals.extend(await self._check_grid_execution(symbol, current_price))

        return signals

    async def _create_grid_orders(self, symbol: str, current_price: float):
        """创建网格订单"""
        for i in range(1, self.grid_levels + 1):
            # 买入网格
            buy_price = current_price * (1 - i * self.grid_spacing)
            sell_price = current_price * (1 + i * self.grid_spacing)

            # 创建买入网格订单
            if buy_price not in self.grid_orders:
                self.grid_orders[buy_price] = {
                    'symbol': symbol,
                    'side': OrderSide.BUY,
                    'quantity': self.config.get('grid_size', 0.1),
                    'price': buy_price,
                    'status': 'pending'
                }

            # 创建卖出网格订单
            if sell_price not in self.grid_orders:
                self.grid_orders[sell_price] = {
                    'symbol': symbol,
                    'side': OrderSide.SELL,
                    'quantity': self.config.get('grid_size', 0.1),
                    'price': sell_price,
                    'status': 'pending'
                }

    async def _check_grid_execution(self, symbol: str, current_price: float) -> List[Signal]:
        """检查网格触发"""
        signals = []

        for price, order_info in self.grid_orders.items():
            if order_info['status'] != 'pending':
                continue

            # 检查价格是否触发网格
            if (order_info['side'] == OrderSide.BUY and current_price <= price) or \
               (order_info['side'] == OrderSide.SELL and current_price >= price):

                signal = Signal(
                    symbol=symbol,
                    side=order_info['side'],
                    action='place_order',
                    strength=1.0,
                    price=price,
                    quantity=order_info['quantity'],
                    reason=f"网格触发 {price}",
                    timestamp=datetime.now()
                )
                signals.append(signal)
                order_info['status'] = 'executed'

        return signals

    async def on_order_filled(self, order: Order):
        """订单成交处理"""
        if order.symbol in self.positions:
            position = self.positions[order.symbol]
            position.updated_at = datetime.now()

    async def on_market_update(self, market_data: Dict[str, Any]):
        """市场数据更新"""
        pass

class TrendFollowingStrategy(BaseStrategy):
    """趋势跟踪策略"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("趋势跟踪策略", config)
        self.ma_short = config.get('ma_short', 10)
        self.ma_long = config.get('ma_long', 20)
        self.rsi_period = config.get('rsi_period', 14)
        self.price_history: Dict[str, List[float]] = {}

    async def analyze_market(self, market_data: Dict[str, Any]) -> List[Signal]:
        """分析趋势"""
        signals = []

        for symbol, data in market_data.items():
            price = data['last_price']

            # 更新价格历史
            if symbol not in self.price_history:
                self.price_history[symbol] = []

            self.price_history[symbol].append(price)

            # 保持历史长度
            if len(self.price_history[symbol]) > self.ma_long:
                self.price_history[symbol].pop(0)

            # 生成信号
            signal = await self._generate_trend_signal(symbol)
            if signal:
                signals.append(signal)

        return signals

    async def _generate_trend_signal(self, symbol: str) -> Optional[Signal]:
        """生成趋势信号"""
        prices = self.price_history[symbol]
        if len(prices) < self.ma_long:
            return None

        # 计算移动平均线
        ma_short = sum(prices[-self.ma_short:]) / self.ma_short
        ma_long = sum(prices[-self.ma_long:]) / self.ma_long

        # 计算简单RSI
        gains = []
        losses = []
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            gains.append(max(0, change))
            losses.append(max(0, -change))

        rsi = 50  # 默认值
        if len(gains) >= self.rsi_period:
            avg_gain = sum(gains[-self.rsi_period:]) / self.rsi_period
            avg_loss = sum(losses[-self.rsi_period:]) / self.rsi_period
            if avg_loss > 0:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

        # 生成信号
        current_price = prices[-1]

        # 金叉买入
        if ma_short > ma_long and rsi < 70:
            return Signal(
                symbol=symbol,
                side=OrderSide.BUY,
                action='buy',
                strength=min(abs(ma_short - ma_long) / ma_long * 10, 1.0),
                price=current_price,
                quantity=self.config.get('position_size', 1.0),
                reason=f"金叉 MA{self.ma_short} > MA{self.ma_long}, RSI={rsi:.2f}",
                timestamp=datetime.now()
            )

        # 死叉卖出
        elif ma_short < ma_long and rsi > 30:
            return Signal(
                symbol=symbol,
                side=OrderSide.SELL,
                action='sell',
                strength=min(abs(ma_short - ma_long) / ma_long * 10, 1.0),
                price=current_price,
                quantity=self.config.get('position_size', 1.0),
                reason=f"死叉 MA{self.ma_short} < MA{self.ma_long}, RSI={rsi:.2f}",
                timestamp=datetime.now()
            )

        return None

    async def on_order_filled(self, order: Order):
        """订单成交处理"""
        pass

    async def on_market_update(self, market_data: Dict[str, Any]):
        """市场数据更新"""
        pass

class ArbitrageStrategy(BaseStrategy):
    """套利策略"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("套利策略", config)
        self.min_profit_rate = config.get('min_profit_rate', 0.001)  # 0.1%
        self.price_tolerance = config.get('price_tolerance', 0.005)  # 0.5%

    async def analyze_market(self, market_data: Dict[str, Any]) -> List[Signal]:
        """分析套利机会"""
        signals = []

        # 假设市场数据包含多个交易对
        pairs = ['ETH/USDT', 'BTC/USDT']

        for i, symbol1 in enumerate(pairs):
            for symbol2 in pairs[i+1:]:
                signal = await self._check_arbitrage(symbol1, symbol2, market_data)
                if signal:
                    signals.append(signal)

        return signals

    async def _check_arbitrage(self, symbol1: str, symbol2: str, market_data: Dict[str, Any]) -> Optional[Signal]:
        """检查套利机会"""
        if symbol1 not in market_data or symbol2 not in market_data:
            return None

        price1 = market_data[symbol1]['last_price']
        price2 = market_data[symbol2]['last_price']

        # 简化的套利逻辑（实际应该更复杂）
        price_diff = abs(price1 - price2)
        avg_price = (price1 + price2) / 2

        if price_diff / avg_price > self.min_profit_rate:
            # 确定哪个价格更高
            if price1 > price2 * (1 + self.price_tolerance):
                return Signal(
                    symbol=symbol1,
                    side=OrderSide.SELL,
                    action='sell',
                    strength=min(price_diff / avg_price, 1.0),
                    price=price1,
                    quantity=1.0,
                    reason=f"{symbol1}价格高于{symbol2}，套利机会",
                    timestamp=datetime.now()
                )
            elif price2 > price1 * (1 + self.price_tolerance):
                return Signal(
                    symbol=symbol2,
                    side=OrderSide.SELL,
                    action='sell',
                    strength=min(price_diff / avg_price, 1.0),
                    price=price2,
                    quantity=1.0,
                    reason=f"{symbol2}价格高于{symbol1}，套利机会",
                    timestamp=datetime.now()
                )

        return None

    async def on_order_filled(self, order: Order):
        """订单成交处理"""
        pass

    async def on_market_update(self, market_data: Dict[str, Any]):
        """市场数据更新"""
        pass