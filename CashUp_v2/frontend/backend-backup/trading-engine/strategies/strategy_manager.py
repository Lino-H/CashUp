"""
策略管理器 - 统一管理和执行所有交易策略
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import asdict

from .base_strategy import BaseStrategy, Signal, Position
from exchanges.base import Order, OrderSide, OrderType, ExchangeManager

logger = logging.getLogger(__name__)

class StrategyManager:
    """策略管理器 - 负责策略的注册、执行和管理"""

    def __init__(self, config_service=None, exchange_manager: ExchangeManager = None):
        self.strategies: Dict[str, BaseStrategy] = {}
        self.config_service = config_service
        self.exchange_manager = exchange_manager
        self.is_running = False
        self.strategy_tasks: Dict[str, asyncio.Task] = {}

    async def initialize(self):
        """初始化策略管理器"""
        logger.info("🚀 初始化策略管理器...")
        self.is_running = True

        # 初始化交易所管理器（如果提供）
        if self.exchange_manager:
            logger.info("📡 交易所管理器已连接")

        # 从配置服务加载策略配置
        if self.config_service:
            try:
                strategies_config = await self.config_service.get_trading_config()
                logger.info(f"📋 从配置服务加载策略配置")
                await self.load_strategies_from_config(strategies_config)
            except Exception as e:
                logger.error(f"从配置加载策略失败: {e}")
                # 使用默认策略
                await self.load_default_strategies()
        else:
            # 使用默认策略
            logger.info("⚠️ 未提供配置服务，使用默认策略")
            await self.load_default_strategies()

        logger.info(f"✅ 策略管理器初始化完成，已加载 {len(self.strategies)} 个策略")

    async def load_default_strategies(self):
        """加载默认策略"""
        # 网格策略
        grid_config = {
            'grid_levels': 5,
            'grid_spacing': 0.02,
            'base_price': 3000.0,
            'grid_size': 0.1,
            'max_position_size': 10.0,
            'stop_loss_rate': 0.05,
            'take_profit_rate': 0.1,
            'position_risk_percent': 2.0
        }

        from .base_strategy import GridStrategy
        grid_strategy = GridStrategy(grid_config)
        await self.register_strategy('grid', grid_strategy)

        # 趋势跟踪策略
        trend_config = {
            'ma_short': 10,
            'ma_long': 20,
            'rsi_period': 14,
            'position_size': 1.0,
            'max_position_size': 10.0,
            'stop_loss_rate': 0.05,
            'take_profit_rate': 0.1,
            'position_risk_percent': 2.0
        }

        from .base_strategy import TrendFollowingStrategy
        trend_strategy = TrendFollowingStrategy(trend_config)
        await self.register_strategy('trend', trend_strategy)

        # 套利策略
        arbitrage_config = {
            'min_profit_rate': 0.001,
            'price_tolerance': 0.005,
            'max_position_size': 5.0,
            'position_risk_percent': 1.0
        }

        from .base_strategy import ArbitrageStrategy
        arbitrage_strategy = ArbitrageStrategy(arbitrage_config)
        await self.register_strategy('arbitrage', arbitrage_strategy)

    async def load_strategies_from_config(self, config: Dict[str, Any]):
        """从配置加载策略"""
        # 从配置中提取策略设置
        strategy_configs = config.get('strategies', {})

        for strategy_name, strategy_config in strategy_configs.items():
            try:
                if strategy_name == 'grid':
                    from .base_strategy import GridStrategy
                    strategy = GridStrategy(strategy_config)
                elif strategy_name == 'trend':
                    from .base_strategy import TrendFollowingStrategy
                    strategy = TrendFollowingStrategy(strategy_config)
                elif strategy_name == 'arbitrage':
                    from .base_strategy import ArbitrageStrategy
                    strategy = ArbitrageStrategy(strategy_config)
                else:
                    logger.warning(f"未知的策略类型: {strategy_name}")
                    continue

                await self.register_strategy(strategy_name, strategy)
                logger.info(f"✅ 从配置加载策略 {strategy_name}")

            except Exception as e:
                logger.error(f"加载策略 {strategy_name} 失败: {e}")

        # 如果配置中没有定义策略，使用默认策略
        if not self.strategies:
            logger.info("配置中未定义策略，使用默认策略")
            await self.load_default_strategies()

    async def register_strategy(self, name: str, strategy: BaseStrategy):
        """注册策略"""
        if name in self.strategies:
            logger.warning(f"策略 {name} 已存在，将被替换")

        self.strategies[name] = strategy
        logger.info(f"📊 策略已注册: {name}")

        # 初始化策略
        await strategy.initialize()

    async def start_strategy(self, name: str) -> bool:
        """启动单个策略"""
        if name not in self.strategies:
            logger.error(f"策略 {name} 不存在")
            return False

        if name in self.strategy_tasks:
            logger.warning(f"策略 {name} 已经在运行")
            return True

        strategy = self.strategies[name]
        task = asyncio.create_task(self._run_strategy_loop(name, strategy))
        self.strategy_tasks[name] = task

        logger.info(f"🚀 策略 {name} 启动成功")
        return True

    async def stop_strategy(self, name: str) -> bool:
        """停止单个策略"""
        if name not in self.strategy_tasks:
            logger.warning(f"策略 {name} 未在运行")
            return True

        task = self.strategy_tasks[name]
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            logger.info(f"🛑 策略 {name} 已停止")

        del self.strategy_tasks[name]
        return True

    async def start_all_strategies(self):
        """启动所有策略"""
        logger.info("🚀 启动所有策略...")

        for name in self.strategies:
            await self.start_strategy(name)

        logger.info(f"✅ 已启动 {len(self.strategy_tasks)} 个策略")

    async def stop_all_strategies(self):
        """停止所有策略"""
        logger.info("🛑 停止所有策略...")

        for name in list(self.strategy_tasks.keys()):
            await self.stop_strategy(name)

        logger.info("✅ 所有策略已停止")

    async def _run_strategy_loop(self, name: str, strategy: BaseStrategy):
        """策略运行循环"""
        while self.is_running and strategy.is_running:
            try:
                # 获取市场数据（这里需要从交易所获取）
                market_data = await self._get_market_data(strategy)

                if market_data:
                    # 分析市场并生成信号
                    signals = await strategy.analyze_market(market_data)

                    # 执行交易信号
                    for signal in signals:
                        await self._execute_signal(signal, strategy)

                # 等待下一个周期
                await asyncio.sleep(1)  # 1秒运行一次

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"策略 {name} 运行出错: {e}")
                await asyncio.sleep(5)  # 出错后等待5秒再重试

    async def _get_market_data(self, strategy: BaseStrategy) -> Optional[Dict[str, Any]]:
        """获取市场数据"""
        if not self.exchange_manager:
            logger.warning("交易所管理器未初始化，无法获取市场数据")
            return None

        try:
            # 从交易所获取当前支持的所有交易对数据
            market_data = {}

            # 假设策略关注BTC/USDT和ETH/USDT
            symbols = ['BTC/USDT', 'ETH/USDT']

            for symbol in symbols:
                # 获取行情数据
                ticker = await self.exchange_manager.get_ticker(symbol)
                if ticker:
                    market_data[symbol] = {
                        'last_price': ticker.last_price,
                        'bid_price': ticker.bid_price,
                        'ask_price': ticker.ask_price,
                        'volume_24h': ticker.volume_24h,
                        'price_change_24h': ticker.price_change_24h,
                        'timestamp': datetime.now().isoformat()
                    }

            return market_data

        except Exception as e:
            logger.error(f"获取市场数据失败: {e}")
            return None

    async def _execute_signal(self, signal: Signal, strategy: BaseStrategy):
        """执行交易信号"""
        logger.info(f"📊 执行交易信号: {signal.symbol} {signal.action} 强度={signal.strength:.2f}")

        # 更新策略持仓
        if signal.action in ['buy', 'sell']:
            order_side = OrderSide.BUY if signal.action == 'buy' else OrderSide.SELL

            # 这里应该实际下单，现在只是模拟
            try:
                if self.exchange_manager and signal.quantity and signal.price:
                    # 创建订单请求
                    from exchanges.base import OrderRequest
                    order_request = OrderRequest(
                        symbol=signal.symbol,
                        side=order_side,
                        type=OrderType.LIMIT,
                        quantity=signal.quantity,
                        price=signal.price,
                        time_in_force='gtc'
                    )

                    # 发送订单
                    order = await self.exchange_manager.place_order(order_request)

                    if order:
                        logger.info(f"✅ 订单创建成功: {order.id}")
                        # 更新策略持仓
                        strategy.update_position(
                            symbol=signal.symbol,
                            side=order_side,
                            size=signal.quantity,
                            price=signal.price
                        )

                        # 回调策略订单成交事件
                        await strategy.on_order_filled(order)
                    else:
                        logger.error("❌ 订单创建失败")

            except Exception as e:
                logger.error(f"执行交易信号失败: {e}")

        # 添加信号到策略
        strategy.add_signal(signal)

    async def get_strategy_status(self) -> Dict[str, Any]:
        """获取所有策略状态"""
        status = {}

        for name, strategy in self.strategies.items():
            status[name] = {
                'name': strategy.name,
                'is_running': strategy.is_running,
                'position_count': len(strategy.positions),
                'signal_count': len(strategy.signals),
                'performance_metrics': strategy.get_performance_metrics(),
                'running': name in self.strategy_tasks
            }

        return status

    async def get_strategy_signals(self, strategy_name: str, limit: int = 10) -> List[Signal]:
        """获取特定策略的交易信号"""
        if strategy_name not in self.strategies:
            return []

        strategy = self.strategies[strategy_name]
        return strategy.get_signals(limit)

    async def get_strategy_positions(self, strategy_name: str) -> List[Position]:
        """获取特定策略的持仓"""
        if strategy_name not in self.strategies:
            return []

        strategy = self.strategies[strategy_name]
        return list(strategy.positions.values())

    async def update_strategy_config(self, name: str, config: Dict[str, Any]):
        """更新策略配置"""
        if name not in self.strategies:
            logger.error(f"策略 {name} 不存在")
            return False

        strategy = self.strategies[name]
        strategy.config.update(config)

        logger.info(f"📝 策略 {name} 配置已更新")
        return True

    async def shutdown(self):
        """关闭策略管理器"""
        logger.info("🔄 关闭策略管理器...")

        self.is_running = False
        await self.stop_all_strategies()

        logger.info("✅ 策略管理器已关闭")

# 全局策略管理器实例
_strategy_manager = None

async def get_strategy_manager() -> StrategyManager:
    """获取全局策略管理器实例"""
    global _strategy_manager

    if _strategy_manager is None:
        _strategy_manager = StrategyManager()
        await _strategy_manager.initialize()

    return _strategy_manager

async def shutdown_strategy_manager():
    """关闭全局策略管理器"""
    global _strategy_manager

    if _strategy_manager:
        await _strategy_manager.shutdown()
        _strategy_manager = None