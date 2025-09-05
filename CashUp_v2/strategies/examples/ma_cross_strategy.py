"""
均线交叉策略示例

使用短期均线和长期均线的交叉来产生交易信号：
- 金叉（短期均线上穿长期均线）：买入信号
- 死叉（短期均线下穿长期均线）：卖出信号
"""

import pandas as pd
import numpy as np
from typing import Optional
from strategy_platform.strategies.base import (
    StrategyBase, StrategyConfig, StrategySignal, SignalType, OrderType, TimeFrame
)

class MACrossStrategy(StrategyBase):
    """
    均线交叉策略
    
    策略逻辑：
    1. 计算短期和长期移动平均线
    2. 当短期均线上穿长期均线时（金叉），产生买入信号
    3. 当短期均线下穿长期均线时（死叉），产生卖出信号
    
    参数：
    - short_period: 短期均线周期（默认：5）
    - long_period: 长期均线周期（默认：20）
    """
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.version = "1.0.0"
        self.author = "CashUp Team"
        self.short_period = 5
        self.long_period = 20
        
        # 从配置中获取参数
        if hasattr(config, 'extra_params'):
            self.short_period = config.extra_params.get('short_period', 5)
            self.long_period = config.extra_params.get('long_period', 20)
        
        # 验证参数
        if self.short_period >= self.long_period:
            raise ValueError("短期均线周期必须小于长期均线周期")
    
    def initialize(self) -> None:
        """策略初始化"""
        print(f"初始化均线交叉策略: {self.name}")
        print(f"短期均线周期: {self.short_period}")
        print(f"长期均线周期: {self.long_period}")
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        data = data.copy()
        
        # 计算移动平均线
        data['ma_short'] = data['close'].rolling(window=self.short_period).mean()
        data['ma_long'] = data['close'].rolling(window=self.long_period).mean()
        
        # 计算均线距离
        data['ma_distance'] = data['ma_short'] - data['ma_long']
        data['ma_distance_pct'] = data['ma_distance'] / data['ma_long'] * 100
        
        # 计算均线交叉信号
        data['signal'] = 0
        data.loc[data['ma_short'] > data['ma_long'], 'signal'] = 1
        data.loc[data['ma_short'] < data['ma_long'], 'signal'] = -1
        
        # 计算信号变化（交叉点）
        data['signal_change'] = data['signal'].diff()
        
        return data
    
    def on_data(self, data: pd.DataFrame) -> Optional[StrategySignal]:
        """处理市场数据，返回交易信号"""
        try:
            # 确保有足够的数据
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
            signal_change = latest['signal_change']
            
            # 金叉：买入信号
            if signal_change > 0:  # 从-1变为1，或从0变为1
                # 计算信号强度
                ma_distance_pct = latest['ma_distance_pct']
                confidence = min(abs(ma_distance_pct) / 2.0, 1.0)  # 最大置信度1.0
                
                return StrategySignal(
                    signal_type=SignalType.BUY,
                    symbol=latest['symbol'],
                    quantity=1.0,
                    price=latest['close'],
                    reason=f"均线金叉 (MA{self.short_period} > MA{self.long_period})",
                    confidence=confidence,
                    metadata={
                        'ma_short': latest['ma_short'],
                        'ma_long': latest['ma_long'],
                        'ma_distance_pct': ma_distance_pct
                    }
                )
            
            # 死叉：卖出信号
            elif signal_change < 0:  # 从1变为-1，或从0变为-1
                # 计算信号强度
                ma_distance_pct = latest['ma_distance_pct']
                confidence = min(abs(ma_distance_pct) / 2.0, 1.0)  # 最大置信度1.0
                
                return StrategySignal(
                    signal_type=SignalType.SELL,
                    symbol=latest['symbol'],
                    quantity=1.0,
                    price=latest['close'],
                    reason=f"均线死叉 (MA{self.short_period} < MA{self.long_period})",
                    confidence=confidence,
                    metadata={
                        'ma_short': latest['ma_short'],
                        'ma_long': latest['ma_long'],
                        'ma_distance_pct': ma_distance_pct
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
        
        print(f"均线交叉策略订单成交: {side} {quantity} {symbol} @ {price}")
        
        # 更新策略状态
        if side == 'buy':
            print(f"建立多头仓位: {symbol}")
        elif side == 'sell':
            print(f"建立空头仓位或平仓: {symbol}")
    
    def on_error(self, error: Exception) -> None:
        """错误处理回调"""
        print(f"均线交叉策略错误: {error}")
        
        # 可以在这里添加错误处理逻辑，如：
        # 1. 发送通知
        # 2. 记录错误日志
        # 3. 调整策略参数
    
    def get_strategy_params(self) -> dict:
        """获取策略参数"""
        return {
            'short_period': self.short_period,
            'long_period': self.long_period,
            'description': f"MA{self.short_period}/MA{self.long_period} 交叉策略"
        }
    
    def optimize_parameters(self, data: pd.DataFrame) -> dict:
        """优化策略参数（简化版）"""
        print(f"开始优化 {self.name} 参数...")
        
        best_params = {
            'short_period': self.short_period,
            'long_period': self.long_period,
            'sharpe_ratio': 0.0
        }
        
        # 简单的参数网格搜索
        for short_period in range(3, 15):
            for long_period in range(short_period + 5, 30):
                try:
                    # 临时设置参数
                    self.short_period = short_period
                    self.long_period = long_period
                    
                    # 计算性能指标（简化版）
                    data_with_indicators = self.calculate_indicators(data)
                    
                    # 计算信号
                    data_with_indicators['signal'] = 0
                    data_with_indicators.loc[data_with_indicators['ma_short'] > data_with_indicators['ma_long'], 'signal'] = 1
                    data_with_indicators.loc[data_with_indicators['ma_short'] < data_with_indicators['ma_long'], 'signal'] = -1
                    
                    # 计算收益率
                    data_with_indicators['returns'] = data_with_indicators['close'].pct_change()
                    data_with_indicators['strategy_returns'] = data_with_indicators['signal'].shift(1) * data_with_indicators['returns']
                    
                    # 计算夏普比率
                    strategy_returns = data_with_indicators['strategy_returns'].dropna()
                    if len(strategy_returns) > 0:
                        sharpe_ratio = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)
                        
                        if sharpe_ratio > best_params['sharpe_ratio']:
                            best_params = {
                                'short_period': short_period,
                                'long_period': long_period,
                                'sharpe_ratio': sharpe_ratio
                            }
                
                except Exception as e:
                    continue
        
        # 恢复最佳参数
        self.short_period = best_params['short_period']
        self.long_period = best_params['long_period']
        
        print(f"参数优化完成:")
        print(f"  短期均线周期: {best_params['short_period']}")
        print(f"  长期均线周期: {best_params['long_period']}")
        print(f"  夏普比率: {best_params['sharpe_ratio']:.2f}")
        
        return best_params