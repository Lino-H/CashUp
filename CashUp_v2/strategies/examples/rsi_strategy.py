"""
RSI超买超卖策略示例

使用RSI指标判断超买超卖状态：
- RSI > 70：超买，卖出信号
- RSI < 30：超卖，买入信号
"""

import pandas as pd
import numpy as np
from typing import Optional
from strategy_platform.strategies.base import (
    StrategyBase, StrategyConfig, StrategySignal, SignalType, OrderType, TimeFrame
)

class RSIStrategy(StrategyBase):
    """
    RSI超买超卖策略
    
    策略逻辑：
    1. 计算RSI指标
    2. 当RSI > 70时，认为市场超买，产生卖出信号
    3. 当RSI < 30时，认为市场超卖，产生买入信号
    4. 当RSI从超买区域回落到50以下时，可以追加买入
    5. 当RSI从超卖区域回升到50以上时，可以追加卖出
    
    参数：
    - rsi_period: RSI计算周期（默认：14）
    - overbought: 超买阈值（默认：70）
    - oversold: 超卖阈值（默认：30）
    - exit_threshold: 出场阈值（默认：50）
    """
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.version = "1.0.0"
        self.author = "CashUp Team"
        self.rsi_period = 14
        self.overbought = 70
        self.oversold = 30
        self.exit_threshold = 50
        
        # 从配置中获取参数
        if hasattr(config, 'extra_params'):
            self.rsi_period = config.extra_params.get('rsi_period', 14)
            self.overbought = config.extra_params.get('overbought', 70)
            self.oversold = config.extra_params.get('oversold', 30)
            self.exit_threshold = config.extra_params.get('exit_threshold', 50)
        
        # 验证参数
        if self.overbought <= self.oversold:
            raise ValueError("超买阈值必须大于超卖阈值")
        if not (30 <= self.oversold <= 50):
            raise ValueError("超卖阈值应在30-50之间")
        if not (50 <= self.overbought <= 70):
            raise ValueError("超买阈值应在50-70之间")
    
    def initialize(self) -> None:
        """策略初始化"""
        print(f"初始化RSI策略: {self.name}")
        print(f"RSI周期: {self.rsi_period}")
        print(f"超买阈值: {self.overbought}")
        print(f"超卖阈值: {self.oversold}")
        print(f"出场阈值: {self.exit_threshold}")
    
    def calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        delta = data['close'].diff()
        
        # 分离涨跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # 计算平均涨跌幅
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # 计算RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        data = data.copy()
        
        # 计算RSI
        data['rsi'] = self.calculate_rsi(data, self.rsi_period)
        
        # 计算RSI移动平均
        data['rsi_ma'] = data['rsi'].rolling(window=9).mean()
        
        # 计算RSI变化率
        data['rsi_change'] = data['rsi'].diff()
        
        # 计算价格变化
        data['price_change'] = data['close'].pct_change()
        
        # 标记超买超卖区域
        data['overbought'] = data['rsi'] > self.overbought
        data['oversold'] = data['rsi'] < self.oversold
        
        # 计算信号强度
        data['buy_strength'] = np.where(data['rsi'] < self.oversold, 
                                      (self.oversold - data['rsi']) / self.oversold, 0)
        data['sell_strength'] = np.where(data['rsi'] > self.overbought, 
                                       (data['rsi'] - self.overbought) / (100 - self.overbought), 0)
        
        return data
    
    def on_data(self, data: pd.DataFrame) -> Optional[StrategySignal]:
        """处理市场数据，返回交易信号"""
        try:
            # 确保有足够的数据
            if len(data) < self.rsi_period:
                return None
            
            # 计算指标
            data_with_indicators = self.calculate_indicators(data)
            
            # 获取最新数据
            latest = data_with_indicators.iloc[-1]
            previous = data_with_indicators.iloc[-2]
            
            current_rsi = latest['rsi']
            previous_rsi = previous['rsi']
            
            # 超卖买入信号
            if current_rsi < self.oversold:
                # 计算信号强度
                buy_strength = latest['buy_strength']
                confidence = min(buy_strength, 1.0)
                
                # RSI从更低位置回升，增强信号
                if previous_rsi < current_rsi and current_rsi < self.oversold * 0.8:
                    confidence = min(confidence * 1.2, 1.0)
                
                return StrategySignal(
                    signal_type=SignalType.BUY,
                    symbol=latest['symbol'],
                    quantity=1.0,
                    price=latest['close'],
                    reason=f"RSI超卖买入 (RSI: {current_rsi:.1f})",
                    confidence=confidence,
                    metadata={
                        'rsi': current_rsi,
                        'rsi_period': self.rsi_period,
                        'oversold': self.oversold,
                        'buy_strength': buy_strength
                    }
                )
            
            # 超买卖出信号
            elif current_rsi > self.overbought:
                # 计算信号强度
                sell_strength = latest['sell_strength']
                confidence = min(sell_strength, 1.0)
                
                # RSI从更高位置回落，增强信号
                if previous_rsi > current_rsi and current_rsi > self.overbought * 1.2:
                    confidence = min(confidence * 1.2, 1.0)
                
                return StrategySignal(
                    signal_type=SignalType.SELL,
                    symbol=latest['symbol'],
                    quantity=1.0,
                    price=latest['close'],
                    reason=f"RSI超买卖出 (RSI: {current_rsi:.1f})",
                    confidence=confidence,
                    metadata={
                        'rsi': current_rsi,
                        'rsi_period': self.rsi_period,
                        'overbought': self.overbought,
                        'sell_strength': sell_strength
                    }
                )
            
            # 从超买区域回落到出场阈值
            elif (previous_rsi > self.overbought and 
                  current_rsi < self.exit_threshold and 
                  current_rsi > self.oversold):
                
                return StrategySignal(
                    signal_type=SignalType.SELL,
                    symbol=latest['symbol'],
                    quantity=0.5,  # 减仓信号
                    price=latest['close'],
                    reason=f"RSI从超买区域回落 (RSI: {current_rsi:.1f})",
                    confidence=0.6,
                    metadata={
                        'rsi': current_rsi,
                        'previous_rsi': previous_rsi,
                        'exit_threshold': self.exit_threshold
                    }
                )
            
            # 从超卖区域回升到出场阈值
            elif (previous_rsi < self.oversold and 
                  current_rsi > self.exit_threshold and 
                  current_rsi < self.overbought):
                
                return StrategySignal(
                    signal_type=SignalType.BUY,
                    symbol=latest['symbol'],
                    quantity=0.5,  # 加仓信号
                    price=latest['close'],
                    reason=f"RSI从超卖区域回升 (RSI: {current_rsi:.1f})",
                    confidence=0.6,
                    metadata={
                        'rsi': current_rsi,
                        'previous_rsi': previous_rsi,
                        'exit_threshold': self.exit_threshold
                    }
                )
            
            return None
            
        except Exception as e:
            self.on_error(e)
            return None
    
    def on_order_filled(self, order: dict) -> None:
        """订单成交回调"""
        symbol = order.get('symbol', 'Unknown')
        side = order.get('side', 'Unknown')
        price = order.get('price', 0)
        quantity = order.get('quantity', 0)
        
        print(f"RSI策略订单成交: {side} {quantity} {symbol} @ {price}")
        
        # 更新策略状态
        if side == 'buy':
            print(f"RSI买入信号执行: {symbol}")
        elif side == 'sell':
            print(f"RSI卖出信号执行: {symbol}")
    
    def on_error(self, error: Exception) -> None:
        """错误处理回调"""
        print(f"RSI策略错误: {error}")
    
    def get_strategy_params(self) -> dict:
        """获取策略参数"""
        return {
            'rsi_period': self.rsi_period,
            'overbought': self.overbought,
            'oversold': self.oversold,
            'exit_threshold': self.exit_threshold,
            'description': f"RSI{self.rsi_period} 超买超卖策略"
        }
    
    def get_rsi_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """获取RSI信号（用于分析）"""
        data_with_indicators = self.calculate_indicators(data)
        
        # 生成信号标记
        data_with_indicators['signal'] = 0
        data_with_indicators.loc[data_with_indicators['rsi'] < self.oversold, 'signal'] = 1
        data_with_indicators.loc[data_with_indicators['rsi'] > self.overbought, 'signal'] = -1
        
        return data_with_indicators
    
    def calculate_optimal_parameters(self, data: pd.DataFrame) -> dict:
        """计算最优参数（简化版）"""
        print(f"开始优化 {self.name} 参数...")
        
        best_params = {
            'rsi_period': self.rsi_period,
            'overbought': self.overbought,
            'oversold': self.oversold,
            'sharpe_ratio': 0.0
        }
        
        # 参数网格搜索
        for rsi_period in [10, 14, 20]:
            for overbought in [65, 70, 75]:
                for oversold in [25, 30, 35]:
                    if overbought <= oversold + 20:  # 确保有足够的间距
                        continue
                    
                    try:
                        # 临时设置参数
                        self.rsi_period = rsi_period
                        self.overbought = overbought
                        self.oversold = oversold
                        
                        # 计算信号
                        signals_df = self.get_rsi_signals(data)
                        
                        # 计算收益率
                        signals_df['returns'] = signals_df['close'].pct_change()
                        signals_df['strategy_returns'] = signals_df['signal'].shift(1) * signals_df['returns']
                        
                        # 计算性能指标
                        strategy_returns = signals_df['strategy_returns'].dropna()
                        if len(strategy_returns) > 0:
                            sharpe_ratio = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)
                            
                            if sharpe_ratio > best_params['sharpe_ratio']:
                                best_params = {
                                    'rsi_period': rsi_period,
                                    'overbought': overbought,
                                    'oversold': oversold,
                                    'sharpe_ratio': sharpe_ratio
                                }
                    
                    except Exception as e:
                        continue
        
        # 恢复最佳参数
        self.rsi_period = best_params['rsi_period']
        self.overbought = best_params['overbought']
        self.oversold = best_params['oversold']
        
        print(f"参数优化完成:")
        print(f"  RSI周期: {best_params['rsi_period']}")
        print(f"  超买阈值: {best_params['overbought']}")
        print(f"  超卖阈值: {best_params['oversold']}")
        print(f"  夏普比率: {best_params['sharpe_ratio']:.2f}")
        
        return best_params