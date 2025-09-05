"""
策略管理器 - 负责策略的加载、运行和管理
"""

import os
import sys
import importlib.util
import inspect
import json
from typing import Dict, List, Optional, Type, Any
from datetime import datetime
import asyncio
from pathlib import Path

from .base import StrategyBase, StrategyConfig, StrategySignal
from ..utils.logger import get_logger

logger = get_logger(__name__)

class StrategyManager:
    """策略管理器"""
    
    def __init__(self, strategies_dir: str = "./strategies"):
        self.strategies_dir = Path(strategies_dir)
        self.loaded_strategies: Dict[str, StrategyBase] = {}
        self.strategy_classes: Dict[str, Type[StrategyBase]] = {}
        self.strategy_metadata: Dict[str, Dict[str, Any]] = {}
        self.running_strategies: Dict[str, asyncio.Task] = {}
        
        # 确保策略目录存在
        self.strategies_dir.mkdir(exist_ok=True)
        
        # 创建子目录
        (self.strategies_dir / "templates").mkdir(exist_ok=True)
        (self.strategies_dir / "examples").mkdir(exist_ok=True)
        (self.strategies_dir / "custom").mkdir(exist_ok=True)
    
    def discover_strategies(self) -> List[str]:
        """发现可用的策略"""
        strategies = []
        
        # 扫描策略目录
        for strategy_file in self.strategies_dir.rglob("*.py"):
            if strategy_file.name.startswith("__"):
                continue
                
            try:
                # 加载策略模块
                module_name = strategy_file.stem
                spec = importlib.util.spec_from_file_location(module_name, strategy_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # 查找策略类
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, StrategyBase) and 
                        obj != StrategyBase):
                        strategies.append(name)
                        self.strategy_classes[name] = obj
                        
                        # 收集策略元数据
                        self.strategy_metadata[name] = {
                            "file_path": str(strategy_file),
                            "module_name": module_name,
                            "class_name": name,
                            "description": obj.__doc__ or "",
                            "version": getattr(obj, 'version', '1.0.0'),
                            "author": getattr(obj, 'author', ''),
                            "created_at": datetime.fromtimestamp(strategy_file.stat().st_ctime).isoformat(),
                            "modified_at": datetime.fromtimestamp(strategy_file.stat().st_mtime).isoformat()
                        }
                        
            except Exception as e:
                logger.error(f"加载策略文件 {strategy_file} 失败: {e}")
        
        logger.info(f"发现 {len(strategies)} 个策略")
        return strategies
    
    def load_strategy(self, strategy_name: str, config: StrategyConfig) -> Optional[StrategyBase]:
        """加载策略实例"""
        try:
            if strategy_name not in self.strategy_classes:
                logger.error(f"策略 {strategy_name} 未找到")
                return None
            
            # 创建策略实例
            strategy_class = self.strategy_classes[strategy_name]
            strategy_instance = strategy_class(config)
            
            # 初始化策略
            strategy_instance.initialize()
            
            # 保存策略实例
            self.loaded_strategies[strategy_name] = strategy_instance
            
            logger.info(f"策略 {strategy_name} 加载成功")
            return strategy_instance
            
        except Exception as e:
            logger.error(f"加载策略 {strategy_name} 失败: {e}")
            return None
    
    def reload_strategy(self, strategy_name: str) -> bool:
        """重新加载策略"""
        try:
            if strategy_name not in self.loaded_strategies:
                logger.error(f"策略 {strategy_name} 未加载")
                return False
            
            # 停止正在运行的策略
            if strategy_name in self.running_strategies:
                self.stop_strategy(strategy_name)
            
            # 获取原策略配置
            old_strategy = self.loaded_strategies[strategy_name]
            old_config = old_strategy.config
            
            # 重新发现策略
            self.discover_strategies()
            
            # 重新加载策略
            new_strategy = self.load_strategy(strategy_name, old_config)
            if new_strategy:
                logger.info(f"策略 {strategy_name} 重新加载成功")
                return True
            else:
                logger.error(f"策略 {strategy_name} 重新加载失败")
                return False
                
        except Exception as e:
            logger.error(f"重新加载策略 {strategy_name} 失败: {e}")
            return False
    
    def unload_strategy(self, strategy_name: str) -> bool:
        """卸载策略"""
        try:
            # 停止正在运行的策略
            if strategy_name in self.running_strategies:
                self.stop_strategy(strategy_name)
            
            # 移除策略实例
            if strategy_name in self.loaded_strategies:
                del self.loaded_strategies[strategy_name]
                logger.info(f"策略 {strategy_name} 卸载成功")
                return True
            else:
                logger.error(f"策略 {strategy_name} 未加载")
                return False
                
        except Exception as e:
            logger.error(f"卸载策略 {strategy_name} 失败: {e}")
            return False
    
    async def start_strategy(self, strategy_name: str, data_provider) -> bool:
        """启动策略"""
        try:
            if strategy_name not in self.loaded_strategies:
                logger.error(f"策略 {strategy_name} 未加载")
                return False
            
            if strategy_name in self.running_strategies:
                logger.warning(f"策略 {strategy_name} 已在运行")
                return True
            
            strategy = self.loaded_strategies[strategy_name]
            
            # 创建策略运行任务
            task = asyncio.create_task(self._run_strategy(strategy, data_provider))
            self.running_strategies[strategy_name] = task
            
            logger.info(f"策略 {strategy_name} 启动成功")
            return True
            
        except Exception as e:
            logger.error(f"启动策略 {strategy_name} 失败: {e}")
            return False
    
    def stop_strategy(self, strategy_name: str) -> bool:
        """停止策略"""
        try:
            if strategy_name not in self.running_strategies:
                logger.warning(f"策略 {strategy_name} 未运行")
                return True
            
            # 取消任务
            task = self.running_strategies[strategy_name]
            task.cancel()
            
            # 等待任务结束
            try:
                asyncio.get_event_loop().run_until_complete(task)
            except asyncio.CancelledError:
                pass
            
            # 移除任务
            del self.running_strategies[strategy_name]
            
            logger.info(f"策略 {strategy_name} 停止成功")
            return True
            
        except Exception as e:
            logger.error(f"停止策略 {strategy_name} 失败: {e}")
            return False
    
    async def _run_strategy(self, strategy: StrategyBase, data_provider) -> None:
        """运行策略"""
        try:
            logger.info(f"开始运行策略 {strategy.name}")
            
            while True:
                try:
                    # 获取市场数据
                    data = await data_provider.get_data(
                        strategy.config.symbols,
                        strategy.config.timeframe
                    )
                    
                    if data is not None:
                        # 处理数据并生成信号
                        signal = strategy.on_data(data)
                        
                        if signal:
                            # 处理交易信号
                            await self._handle_signal(strategy, signal)
                    
                    # 等待下一个时间周期
                    await asyncio.sleep(self._get_sleep_time(strategy.config.timeframe))
                    
                except asyncio.CancelledError:
                    logger.info(f"策略 {strategy.name} 被取消")
                    break
                except Exception as e:
                    logger.error(f"策略 {strategy.name} 运行错误: {e}")
                    strategy.on_error(e)
                    await asyncio.sleep(1)  # 错误后等待1秒
                    
        except Exception as e:
            logger.error(f"策略 {strategy.name} 运行失败: {e}")
    
    async def _handle_signal(self, strategy: StrategyBase, signal: StrategySignal) -> None:
        """处理交易信号"""
        try:
            logger.info(f"策略 {strategy.name} 生成信号: {signal.signal_type.value} {signal.symbol}")
            
            # 风险管理
            if not strategy.risk_management(signal):
                logger.warning(f"策略 {strategy.name} 信号被风险管理阻止")
                return
            
            # 计算仓位大小
            position_size = strategy.calculate_position_size(signal)
            signal.quantity = position_size
            
            # 这里应该调用交易引擎执行订单
            # order_result = await self.trading_engine.place_order(signal)
            # strategy.on_order_filled(order_result)
            
            logger.info(f"策略 {strategy.name} 信号处理完成")
            
        except Exception as e:
            logger.error(f"处理策略信号失败: {e}")
            strategy.on_error(e)
    
    def _get_sleep_time(self, timeframe) -> float:
        """获取睡眠时间"""
        timeframe_map = {
            "1m": 60,
            "5m": 300,
            "15m": 900,
            "30m": 1800,
            "1h": 3600,
            "4h": 14400,
            "1d": 86400,
            "1w": 604800
        }
        return timeframe_map.get(timeframe.value, 60)
    
    def get_strategy_info(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """获取策略信息"""
        if strategy_name in self.loaded_strategies:
            strategy = self.loaded_strategies[strategy_name]
            return strategy.get_info()
        elif strategy_name in self.strategy_metadata:
            return self.strategy_metadata[strategy_name]
        else:
            return None
    
    def get_all_strategies(self) -> Dict[str, Dict[str, Any]]:
        """获取所有策略信息"""
        strategies = {}
        
        # 已加载的策略
        for name, strategy in self.loaded_strategies.items():
            strategies[name] = strategy.get_info()
            strategies[name]["status"] = "loaded"
            if name in self.running_strategies:
                strategies[name]["status"] = "running"
        
        # 未加载的策略
        for name, metadata in self.strategy_metadata.items():
            if name not in strategies:
                strategies[name] = metadata
                strategies[name]["status"] = "discovered"
        
        return strategies
    
    def get_running_strategies(self) -> List[str]:
        """获取正在运行的策略列表"""
        return list(self.running_strategies.keys())
    
    def validate_strategy_code(self, strategy_code: str) -> Dict[str, Any]:
        """验证策略代码"""
        result = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "strategy_class": None
        }
        
        try:
            # 创建临时文件
            temp_file = self.strategies_dir / "temp_strategy.py"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(strategy_code)
            
            # 尝试加载策略
            spec = importlib.util.spec_from_file_location("temp_strategy", temp_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找策略类
            strategy_classes = []
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, StrategyBase) and 
                    obj != StrategyBase):
                    strategy_classes.append(obj)
            
            if len(strategy_classes) == 0:
                result["errors"].append("未找到策略类，请确保继承自StrategyBase")
            elif len(strategy_classes) > 1:
                result["warnings"].append("发现多个策略类，将使用第一个")
            
            if strategy_classes:
                result["valid"] = True
                result["strategy_class"] = strategy_classes[0]
            
            # 清理临时文件
            temp_file.unlink()
            
        except Exception as e:
            result["errors"].append(f"代码验证失败: {str(e)}")
        
        return result
    
    def create_strategy_template(self, strategy_name: str, strategy_type: str = "basic") -> str:
        """创建策略模板"""
        templates = {
            "basic": self._get_basic_template(),
            "ma_cross": self._get_ma_cross_template(),
            "rsi": self._get_rsi_template(),
            "grid": self._get_grid_template()
        }
        
        template = templates.get(strategy_type, templates["basic"])
        return template.replace("{STRATEGY_NAME}", strategy_name)
    
    def _get_basic_template(self) -> str:
        """获取基础策略模板"""
        return '''
import pandas as pd
from typing import Optional
from strategy_platform.strategies.base import StrategyBase, StrategyConfig, StrategySignal, SignalType, OrderType

class {STRATEGY_NAME}(StrategyBase):
    """
    基础策略模板
    
    这是一个简单的策略模板，用于演示如何创建自定义策略。
    """
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.version = "1.0.0"
        self.author = "Your Name"
    
    def initialize(self) -> None:
        """策略初始化"""
        print(f"初始化策略: {self.name}")
        # 在这里进行策略的初始化工作
        # 例如：初始化指标参数、设置初始状态等
    
    def on_data(self, data: pd.DataFrame) -> Optional[StrategySignal]:
        """
        处理市场数据，返回交易信号
        
        Args:
            data: 市场数据，包含OHLCV等信息
            
        Returns:
            交易信号，如果没有信号则返回None
        """
        try:
            # 确保数据不为空
            if data.empty:
                return None
            
            # 获取最新数据
            latest = data.iloc[-1]
            
            # 在这里实现你的策略逻辑
            # 例如：计算指标、生成交易信号等
            
            # 示例：简单的价格突破策略
            if len(data) > 20:
                # 计算20日移动平均
                ma20 = data['close'].rolling(window=20).mean()
                current_price = latest['close']
                ma20_current = ma20.iloc[-1]
                
                # 生成交易信号
                if current_price > ma20_current:
                    return StrategySignal(
                        signal_type=SignalType.BUY,
                        symbol=latest['symbol'],
                        quantity=1.0,
                        reason="价格突破20日均线",
                        confidence=0.8
                    )
                elif current_price < ma20_current:
                    return StrategySignal(
                        signal_type=SignalType.SELL,
                        symbol=latest['symbol'],
                        quantity=1.0,
                        reason="价格跌破20日均线",
                        confidence=0.8
                    )
            
            return None
            
        except Exception as e:
            self.on_error(e)
            return None
    
    def on_order_filled(self, order: dict) -> None:
        """订单成交回调"""
        print(f"订单成交: {order}")
        # 在这里处理订单成交后的逻辑
        # 例如：更新持仓、记录交易等
    
    def on_error(self, error: Exception) -> None:
        """错误处理回调"""
        print(f"策略错误: {error}")
        # 在这里处理错误
        # 例如：记录日志、发送通知等
'''
    
    def _get_ma_cross_template(self) -> str:
        """获取均线交叉策略模板"""
        return '''
import pandas as pd
from typing import Optional
from strategy_platform.strategies.base import StrategyBase, StrategyConfig, StrategySignal, SignalType, OrderType

class {STRATEGY_NAME}(StrategyBase):
    """
    均线交叉策略
    
    使用短期均线和长期均线的交叉来产生交易信号。
    - 金叉（短期均线上穿长期均线）：买入信号
    - 死叉（短期均线下穿长期均线）：卖出信号
    """
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.version = "1.0.0"
        self.author = "Your Name"
        self.short_period = 5  # 短期均线周期
        self.long_period = 20   # 长期均线周期
    
    def initialize(self) -> None:
        """策略初始化"""
        print(f"初始化均线交叉策略: {self.name}")
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        data = data.copy()
        
        # 计算移动平均线
        data['ma_short'] = data['close'].rolling(window=self.short_period).mean()
        data['ma_long'] = data['close'].rolling(window=self.long_period).mean()
        
        # 计算均线交叉信号
        data['signal'] = 0
        data.loc[data['ma_short'] > data['ma_long'], 'signal'] = 1
        data.loc[data['ma_short'] < data['ma_long'], 'signal'] = -1
        
        return data
    
    def on_data(self, data: pd.DataFrame) -> Optional[StrategySignal]:
        """处理市场数据"""
        try:
            if len(data) < self.long_period:
                return None
            
            # 计算指标
            data_with_indicators = self.calculate_indicators(data)
            
            # 获取最新数据
            latest = data_with_indicators.iloc[-1]
            previous = data_with_indicators.iloc[-2]
            
            # 检查均线交叉
            current_signal = latest['signal']
            previous_signal = previous['signal']
            
            # 金叉：买入信号
            if previous_signal == -1 and current_signal == 1:
                return StrategySignal(
                    signal_type=SignalType.BUY,
                    symbol=latest['symbol'],
                    quantity=1.0,
                    reason="均线金叉",
                    confidence=0.8
                )
            
            # 死叉：卖出信号
            elif previous_signal == 1 and current_signal == -1:
                return StrategySignal(
                    signal_type=SignalType.SELL,
                    symbol=latest['symbol'],
                    quantity=1.0,
                    reason="均线死叉",
                    confidence=0.8
                )
            
            return None
            
        except Exception as e:
            self.on_error(e)
            return None
    
    def on_order_filled(self, order: dict) -> None:
        """订单成交回调"""
        print(f"订单成交: {order}")
    
    def on_error(self, error: Exception) -> None:
        """错误处理回调"""
        print(f"策略错误: {error}")
'''
    
    def _get_rsi_template(self) -> str:
        """获取RSI策略模板"""
        return '''
import pandas as pd
import numpy as np
from typing import Optional
from strategy_platform.strategies.base import StrategyBase, StrategyConfig, StrategySignal, SignalType, OrderType

class {STRATEGY_NAME}(StrategyBase):
    """
    RSI超买超卖策略
    
    使用RSI指标判断超买超卖状态：
    - RSI > 70：超卖，卖出信号
    - RSI < 30：超买，买入信号
    """
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.version = "1.0.0"
        self.author = "Your Name"
        self.rsi_period = 14    # RSI周期
        self.overbought = 70   # 超买线
        self.oversold = 30     # 超卖线
    
    def initialize(self) -> None:
        """策略初始化"""
        print(f"初始化RSI策略: {self.name}")
    
    def calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def on_data(self, data: pd.DataFrame) -> Optional[StrategySignal]:
        """处理市场数据"""
        try:
            if len(data) < self.rsi_period:
                return None
            
            # 计算RSI
            data = data.copy()
            data['rsi'] = self.calculate_rsi(data, self.rsi_period)
            
            # 获取最新数据
            latest = data.iloc[-1]
            current_rsi = latest['rsi']
            
            # RSI超买：卖出信号
            if current_rsi > self.overbought:
                return StrategySignal(
                    signal_type=SignalType.SELL,
                    symbol=latest['symbol'],
                    quantity=1.0,
                    reason=f"RSI超买 ({current_rsi:.2f})",
                    confidence=0.7
                )
            
            # RSI超卖：买入信号
            elif current_rsi < self.oversold:
                return StrategySignal(
                    signal_type=SignalType.BUY,
                    symbol=latest['symbol'],
                    quantity=1.0,
                    reason=f"RSI超卖 ({current_rsi:.2f})",
                    confidence=0.7
                )
            
            return None
            
        except Exception as e:
            self.on_error(e)
            return None
    
    def on_order_filled(self, order: dict) -> None:
        """订单成交回调"""
        print(f"订单成交: {order}")
    
    def on_error(self, error: Exception) -> None:
        """错误处理回调"""
        print(f"策略错误: {error}")
'''
    
    def _get_grid_template(self) -> str:
        """获取网格交易策略模板"""
        return '''
import pandas as pd
from typing import Optional, List
from strategy_platform.strategies.base import StrategyBase, StrategyConfig, StrategySignal, SignalType, OrderType

class {STRATEGY_NAME}(StrategyBase):
    """
    网格交易策略
    
    在价格波动范围内设置买入和卖出网格，通过价格波动获利。
    """
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.version = "1.0.0"
        self.author = "Your Name"
        self.grid_spacing = 0.01  # 网格间距 (1%)
        self.grid_levels = 10      # 网格层数
        self.base_price = 0.0       # 基准价格
        self.grid_orders = []       # 网格订单
    
    def initialize(self) -> None:
        """策略初始化"""
        print(f"初始化网格交易策略: {self.name}")
        self.setup_grid()
    
    def setup_grid(self) -> None:
        """设置网格"""
        # 获取当前价格作为基准价格
        if self.config.symbols:
            self.base_price = self.get_current_price(self.config.symbols[0])
        
        if self.base_price > 0:
            # 创建网格订单
            self.grid_orders = []
            
            # 买入网格（低于基准价格）
            for i in range(1, self.grid_levels + 1):
                price = self.base_price * (1 - i * self.grid_spacing)
                self.grid_orders.append({
                    'price': price,
                    'type': 'buy',
                    'quantity': 1.0 / i,  # 越低价格买入越多
                    'filled': False
                })
            
            # 卖出网格（高于基准价格）
            for i in range(1, self.grid_levels + 1):
                price = self.base_price * (1 + i * self.grid_spacing)
                self.grid_orders.append({
                    'price': price,
                    'type': 'sell',
                    'quantity': 1.0 / i,  # 越高价格卖出越多
                    'filled': False
                })
    
    def on_data(self, data: pd.DataFrame) -> Optional[StrategySignal]:
        """处理市场数据"""
        try:
            if data.empty:
                return None
            
            latest = data.iloc[-1]
            current_price = latest['close']
            
            # 检查网格订单
            for order in self.grid_orders:
                if not order['filled']:
                    if (order['type'] == 'buy' and current_price <= order['price']) or \
                       (order['type'] == 'sell' and current_price >= order['price']):
                        
                        # 生成交易信号
                        signal_type = SignalType.BUY if order['type'] == 'buy' else SignalType.SELL
                        
                        return StrategySignal(
                            signal_type=signal_type,
                            symbol=latest['symbol'],
                            quantity=order['quantity'],
                            price=order['price'],
                            order_type=OrderType.LIMIT,
                            reason=f"网格交易触发 (价格: {order['price']})",
                            confidence=0.9
                        )
            
            return None
            
        except Exception as e:
            self.on_error(e)
            return None
    
    def on_order_filled(self, order: dict) -> None:
        """订单成交回调"""
        print(f"网格订单成交: {order}")
        
        # 更新网格订单状态
        for grid_order in self.grid_orders:
            if (abs(grid_order['price'] - order.get('price', 0)) < 0.01 and 
                grid_order['type'] == order.get('side', '')):
                grid_order['filled'] = True
                break
    
    def on_error(self, error: Exception) -> None:
        """错误处理回调"""
        print(f"策略错误: {error}")
'''