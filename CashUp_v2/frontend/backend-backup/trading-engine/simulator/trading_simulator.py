"""
交易模拟器 - 提供安全的模拟交易环境
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
import logging

from ..exchanges.base import (
    Order, OrderRequest, CancelOrderRequest, OrderStatus, OrderSide, OrderType,
    Position, Balance, Ticker, Trade, FundingRate, TimeInForce
)

logger = logging.getLogger(__name__)

@dataclass
class SimulatedOrder:
    """模拟订单"""
    id: str
    client_order_id: str
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: Optional[float]
    stop_price: Optional[float]
    time_in_force: TimeInForce
    status: OrderStatus
    filled_quantity: float
    remaining_quantity: float
    average_price: Optional[float]
    commission: float
    created_at: datetime
    updated_at: datetime
    simulated: bool = True

@dataclass
class SimulatedTrade:
    """模拟成交"""
    id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    commission: float
    timestamp: datetime
    simulated: bool = True

class TradingSimulator:
    """交易模拟器"""

    def __init__(self, initial_balance: Dict[str, float] = None):
        # 模拟账户状态
        self.balances: Dict[str, Balance] = {}
        self.positions: Dict[str, Position] = {}
        self.orders: Dict[str, SimulatedOrder] = {}
        self.trades: List[SimulatedTrade] = []

        # 市场数据
        self.market_data: Dict[str, Ticker] = {}
        self.funding_rates: Dict[str, FundingRate] = {}

        # 模拟参数
        self.commission_rate = 0.001  # 0.1%手续费
        self.initial_balance = initial_balance or {'USDT': 10000.0}

        # 订单队列
        self.pending_orders: List[SimulatedOrder] = []
        self.execution_history: List[Dict] = []

        # 运行状态
        self.is_running = False
        self.simulation_speed = 1.0  # 模拟速度倍数

        # 初始化账户
        self._initialize_account()

    def _initialize_account(self):
        """初始化模拟账户"""
        for asset, amount in self.initial_balance.items():
            self.balances[asset] = Balance(
                asset=asset,
                free=amount,
                used=0.0,
                total=amount
            )
        logger.info(f"模拟账户初始化完成: 初始余额 {self.initial_balance}")

    async def start_simulation(self):
        """启动模拟环境"""
        self.is_running = True
        logger.info("交易模拟器启动")

    async def stop_simulation(self):
        """停止模拟环境"""
        self.is_running = False
        logger.info("交易模拟器停止")

    def get_account_balance(self) -> Dict[str, Balance]:
        """获取账户余额"""
        return self.balances.copy()

    def get_positions(self, symbol: Optional[str] = None) -> List[Position]:
        """获取持仓信息"""
        if symbol:
            return [pos for pos in self.positions.values() if pos.symbol == symbol]
        return list(self.positions.values())

    def get_orders(self, symbol: Optional[str] = None, status: Optional[OrderStatus] = None) -> List[SimulatedOrder]:
        """获取订单列表"""
        orders = list(self.orders.values())

        if symbol:
            orders = [order for order in orders if order.symbol == symbol]

        if status:
            orders = [order for order in orders if order.status == status]

        return orders

    async def create_order(self, request: OrderRequest) -> SimulatedOrder:
        """创建模拟订单"""
        if not self.validate_order_request(request):
            raise ValueError("无效的下单请求")

        # 生成订单ID
        order_id = str(uuid.uuid4())
        client_order_id = request.client_order_id or f"SIM_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{order_id[:8]}"

        # 检查余额/保证金
        if not self._check_order_requirements(request):
            raise ValueError("账户余额不足或保证金不够")

        # 创建模拟订单
        order = SimulatedOrder(
            id=order_id,
            client_order_id=client_order_id,
            symbol=request.symbol,
            side=request.side,
            type=request.type,
            quantity=request.quantity,
            price=request.price,
            stop_price=request.stop_price,
            time_in_force=request.time_in_force,
            status=OrderStatus.OPEN,
            filled_quantity=0.0,
            remaining_quantity=request.quantity,
            average_price=None,
            commission=0.0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # 保存订单
        self.orders[order_id] = order
        self.pending_orders.append(order)

        # 记录执行历史
        self.execution_history.append({
            'timestamp': datetime.now(),
            'action': 'create_order',
            'order_id': order_id,
            'symbol': request.symbol,
            'side': request.side.value,
            'quantity': request.quantity,
            'price': request.price
        })

        logger.info(f"创建模拟订单: {order_id} - {request.symbol} {request.side.value} {request.quantity}")
        return order

    async def cancel_order(self, request: CancelOrderRequest) -> bool:
        """取消模拟订单"""
        # 查找订单
        order = None
        if request.order_id:
            order = self.orders.get(request.order_id)
        elif request.client_order_id:
            for o in self.orders.values():
                if o.client_order_id == request.client_order_id:
                    order = o
                    break

        if not order:
            raise ValueError("订单不存在")

        if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
            return False

        # 更新订单状态
        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.now()
        order.remaining_quantity = order.filled_quantity

        # 从待执行队列中移除
        if order in self.pending_orders:
            self.pending_orders.remove(order)

        # 记录执行历史
        self.execution_history.append({
            'timestamp': datetime.now(),
            'action': 'cancel_order',
            'order_id': order.id,
            'symbol': order.symbol
        })

        logger.info(f"取消模拟订单: {order.id}")
        return True

    async def update_market_data(self, market_data: Dict[str, Ticker]):
        """更新市场数据"""
        self.market_data.update(market_data)
        logger.info(f"更新市场数据: {len(market_data)} 个交易对")

    async def process_market_updates(self):
        """处理市场数据更新，触发订单执行"""
        if not self.is_running:
            return

        for order in self.pending_orders[:]:  # 复制列表避免修改时的问题
            if order.status != OrderStatus.OPEN:
                continue

            # 模拟订单执行逻辑
            await self._simulate_order_execution(order)

    async def _simulate_order_execution(self, order: SimulatedOrder):
        """模拟订单执行"""
        try:
            # 获取当前市场数据
            ticker = self.market_data.get(order.symbol)
            if not ticker:
                return  # 没有市场数据，无法执行

            execution_probability = self._get_execution_probability(order, ticker)

            # 根据订单类型和执行概率决定是否成交
            if order.type == OrderType.MARKET:
                # 市价单立即成交
                await self._execute_order(order, ticker.last_price)
            elif order.type == OrderType.LIMIT:
                # 限价根据价格和市场情况决定
                if order.side == OrderSide.BUY and order.price >= ticker.last_price:
                    await self._execute_order(order, ticker.last_price)
                elif order.side == OrderSide.SELL and order.price <= ticker.last_price:
                    await self._execute_order(order, ticker.last_price)
                else:
                    # 部分成交检查
                    if await self._check_partial_fill(order, ticker):
                        await self._partial_fill_order(order, ticker)

        except Exception as e:
            logger.error(f"模拟订单执行失败 {order.id}: {e}")

    def _get_execution_probability(self, order: SimulatedOrder, ticker: Ticker) -> float:
        """获取订单执行概率"""
        base_probability = 0.1  # 基础10%执行概率

        # 根据订单类型调整
        if order.type == OrderType.MARKET:
            base_probability = 0.8  # 市价单执行概率更高
        elif order.type == OrderType.LIMIT:
            # 限价单距离现价越近，执行概率越高
            if order.price:
                spread_ratio = abs(order.price - ticker.last_price) / ticker.last_price
                base_probability = max(0.05, 0.5 - spread_ratio * 2)

        return min(0.9, base_probability)

    async def _execute_order(self, order: SimulatedOrder, execution_price: float):
        """完全执行订单"""
        # 计算手续费
        commission = order.quantity * execution_price * self.commission_rate

        # 更新订单状态
        order.filled_quantity = order.quantity
        order.remaining_quantity = 0.0
        order.average_price = execution_price
        order.commission = commission
        order.status = OrderStatus.FILLED
        order.updated_at = datetime.now()

        # 从待执行队列中移除
        if order in self.pending_orders:
            self.pending_orders.remove(order)

        # 更新账户余额和持仓
        await self._update_account_after_fill(order, execution_price, commission)

        # 创建模拟成交记录
        trade = SimulatedTrade(
            id=str(uuid.uuid4()),
            order_id=order.id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=execution_price,
            commission=commission,
            timestamp=datetime.now()
        )
        self.trades.append(trade)

        # 记录执行历史
        self.execution_history.append({
            'timestamp': datetime.now(),
            'action': 'fill_order',
            'order_id': order.id,
            'symbol': order.symbol,
            'quantity': order.quantity,
            'price': execution_price
        })

        logger.info(f"模拟订单完全执行: {order.id} 价格={execution_price} 数量={order.quantity}")

    async def _partial_fill_order(self, order: SimulatedOrder, ticker: Ticker):
        """部分执行订单"""
        # 随机决定部分成交数量 (10%-50%)
        fill_ratio = 0.1 + (hash(order.id) % 40) / 100  # 10%-50%
        fill_quantity = order.quantity * fill_ratio

        execution_price = ticker.last_price
        commission = fill_quantity * execution_price * self.commission_rate

        # 更新订单状态
        order.filled_quantity += fill_quantity
        order.remaining_quantity -= fill_quantity
        order.average_price = execution_price
        order.commission += commission
        order.updated_at = datetime.now()

        # 更新账户余额
        await self._update_account_after_fill(order, execution_price, commission)

        # 创建部分成交记录
        trade = SimulatedTrade(
            id=str(uuid.uuid4()),
            order_id=order.id,
            symbol=order.symbol,
            side=order.side,
            quantity=fill_quantity,
            price=execution_price,
            commission=commission,
            timestamp=datetime.now()
        )
        self.trades.append(trade)

        # 记录执行历史
        self.execution_history.append({
            'timestamp': datetime.now(),
            'action': 'partial_fill',
            'order_id': order.id,
            'symbol': order.symbol,
            'quantity': fill_quantity,
            'price': execution_price
        })

        logger.info(f"模拟订单部分执行: {order.id} 价格={execution_price} 数量={fill_quantity}")

    def _check_partial_fill(self, order: SimulatedOrder, ticker: Ticker) -> bool:
        """检查是否可能部分成交"""
        # 30%概率部分成交
        return hash(f"{order.id}_{ticker.last_price}") % 100 < 30

    async def _update_account_after_fill(self, order: SimulatedOrder, execution_price: float, commission: float):
        """订单成交后更新账户状态"""
        # 更新余额
        quote_asset = order.symbol.split('/')[1]
        base_asset = order.symbol.split('/')[0]

        if order.side == OrderSide.BUY:
            # 买入，扣除USDT
            usdt_amount = order.quantity * execution_price + commission
            if quote_asset in self.balances:
                if self.balances[quote_asset].free < usdt_amount:
                    raise ValueError("USDT余额不足")
                self.balances[quote_asset].free -= usdt_amount
                self.balances[quote_asset].used += 0.0  # 模拟中不考虑挂单占用
                self.balances[quote_asset].total -= usdt_amount

        else:  # SELL
            # 卖出，扣除币
            if base_asset in self.balances:
                if self.balances[base_asset].free < order.quantity:
                    raise ValueError(f"{base_asset}余额不足")
                self.balances[base_asset].free -= order.quantity
                self.balances[base_asset].used += 0.0
                self.balances[base_asset].total -= order.quantity

        # 更新持仓
        await self._update_position(order, execution_price)

    async def _update_position(self, order: SimulatedOrder, execution_price: float):
        """更新持仓信息"""
        symbol = order.symbol
        if order.side == OrderSide.BUY:
            # 买入持仓
            if symbol not in self.positions:
                self.positions[symbol] = Position(
                    symbol=symbol,
                    side='long',
                    size=0.0,
                    entry_price=0.0,
                    mark_price=execution_price,
                    liquidation_price=0.0,
                    unrealized_pnl=0.0,
                    realized_pnl=0.0,
                    leverage=1,
                    margin_used=0.0,
                    timestamp=datetime.now(),
                    exchange='simulator'
                )

            position = self.positions[symbol]
            position.size += order.quantity
            position.mark_price = execution_price
            # 简化计算：平均持仓成本
            total_cost = position.size * position.entry_price + order.quantity * execution_price
            position.entry_price = total_cost / position.size if position.size > 0 else execution_price

        else:  # SELL
            # 卖出持仓
            if symbol in self.positions:
                position = self.positions[symbol]
                position.size -= order.quantity
                position.mark_price = execution_price

                # 如果持仓为0，删除持仓记录
                if abs(position.size) < 1e-8:  # 考虑浮点精度
                    del self.positions[symbol]

    def validate_order_request(self, request: OrderRequest) -> bool:
        """验证下单请求"""
        if not request.symbol or request.quantity <= 0:
            return False

        if request.type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and not request.price:
            return False

        return True

    def _check_order_requirements(self, request: OrderRequest) -> bool:
        """检查订单要求（余额、保证金等）"""
        quote_asset = request.symbol.split('/')[1]

        if request.side == OrderSide.BUY:
            # 买入需要足够的USDT
            required_amount = request.quantity * (request.price or 0)
            if quote_asset in self.balances:
                return self.balances[quote_asset].free >= required_amount

        return True

    def get_simulation_statistics(self) -> Dict[str, Any]:
        """获取模拟统计信息"""
        return {
            'total_orders': len(self.orders),
            'filled_orders': len([o for o in self.orders.values() if o.status == OrderStatus.FILLED]),
            'open_orders': len([o for o in self.orders.values() if o.status == OrderStatus.OPEN]),
            'total_trades': len(self.trades),
            'total_commission': sum(t.commission for t in self.trades),
            'simulated_positions': len(self.positions),
            'account_balance': sum(b.total for b in self.balances.values()),
            'simulation_start': min((e['timestamp'] for e in self.execution_history), default=datetime.now()),
            'simulation_end': max((e['timestamp'] for e in self.execution_history), default=datetime.now())
        }

    def export_trade_history(self) -> List[Dict]:
        """导出交易历史"""
        return [asdict(trade) for trade in self.trades]

    def get_order_history(self) -> List[Dict]:
        """获取订单历史"""
        return [asdict(order) for order in self.orders.values()]