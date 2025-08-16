#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证器工具

提供各种数据验证功能。
"""

import re
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """
    验证错误异常
    """
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(message)
        self.message = message
        self.field = field
        self.value = value


def validate_strategy_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证策略配置
    
    Args:
        config: 策略配置字典
        
    Returns:
        Dict[str, Any]: 验证后的配置
        
    Raises:
        ValidationError: 验证失败时抛出
    """
    if not isinstance(config, dict):
        raise ValidationError("策略配置必须是字典类型", "config", config)
    
    # 必需字段
    required_fields = ['strategy_type', 'parameters']
    for field in required_fields:
        if field not in config:
            raise ValidationError(f"缺少必需字段: {field}", field)
    
    # 验证策略类型
    valid_strategy_types = [
        'trend_following', 'mean_reversion', 'momentum', 'arbitrage',
        'market_making', 'statistical_arbitrage', 'pairs_trading', 'custom'
    ]
    
    strategy_type = config['strategy_type']
    if strategy_type not in valid_strategy_types:
        raise ValidationError(
            f"无效的策略类型: {strategy_type}",
            "strategy_type",
            strategy_type
        )
    
    # 验证参数
    parameters = config['parameters']
    if not isinstance(parameters, dict):
        raise ValidationError(
            "策略参数必须是字典类型",
            "parameters",
            parameters
        )
    
    # 根据策略类型验证特定参数
    if strategy_type == 'trend_following':
        _validate_trend_following_params(parameters)
    elif strategy_type == 'mean_reversion':
        _validate_mean_reversion_params(parameters)
    elif strategy_type == 'momentum':
        _validate_momentum_params(parameters)
    elif strategy_type == 'arbitrage':
        _validate_arbitrage_params(parameters)
    elif strategy_type == 'market_making':
        _validate_market_making_params(parameters)
    
    # 验证可选字段
    if 'risk_management' in config:
        _validate_risk_management_config(config['risk_management'])
    
    if 'execution' in config:
        _validate_execution_config(config['execution'])
    
    return config


def _validate_trend_following_params(params: Dict[str, Any]) -> None:
    """
    验证趋势跟踪策略参数
    
    Args:
        params: 策略参数
        
    Raises:
        ValidationError: 验证失败时抛出
    """
    required_params = ['lookback_period', 'signal_threshold']
    
    for param in required_params:
        if param not in params:
            raise ValidationError(f"趋势跟踪策略缺少参数: {param}", param)
    
    # 验证回看期间
    lookback_period = params['lookback_period']
    if not isinstance(lookback_period, int) or lookback_period <= 0:
        raise ValidationError(
            "回看期间必须是正整数",
            "lookback_period",
            lookback_period
        )
    
    # 验证信号阈值
    signal_threshold = params['signal_threshold']
    if not isinstance(signal_threshold, (int, float)) or signal_threshold <= 0:
        raise ValidationError(
            "信号阈值必须是正数",
            "signal_threshold",
            signal_threshold
        )


def _validate_mean_reversion_params(params: Dict[str, Any]) -> None:
    """
    验证均值回归策略参数
    
    Args:
        params: 策略参数
        
    Raises:
        ValidationError: 验证失败时抛出
    """
    required_params = ['window_size', 'deviation_threshold']
    
    for param in required_params:
        if param not in params:
            raise ValidationError(f"均值回归策略缺少参数: {param}", param)
    
    # 验证窗口大小
    window_size = params['window_size']
    if not isinstance(window_size, int) or window_size <= 1:
        raise ValidationError(
            "窗口大小必须是大于1的整数",
            "window_size",
            window_size
        )
    
    # 验证偏差阈值
    deviation_threshold = params['deviation_threshold']
    if not isinstance(deviation_threshold, (int, float)) or deviation_threshold <= 0:
        raise ValidationError(
            "偏差阈值必须是正数",
            "deviation_threshold",
            deviation_threshold
        )


def _validate_momentum_params(params: Dict[str, Any]) -> None:
    """
    验证动量策略参数
    
    Args:
        params: 策略参数
        
    Raises:
        ValidationError: 验证失败时抛出
    """
    required_params = ['momentum_period', 'entry_threshold']
    
    for param in required_params:
        if param not in params:
            raise ValidationError(f"动量策略缺少参数: {param}", param)
    
    # 验证动量周期
    momentum_period = params['momentum_period']
    if not isinstance(momentum_period, int) or momentum_period <= 0:
        raise ValidationError(
            "动量周期必须是正整数",
            "momentum_period",
            momentum_period
        )
    
    # 验证入场阈值
    entry_threshold = params['entry_threshold']
    if not isinstance(entry_threshold, (int, float)):
        raise ValidationError(
            "入场阈值必须是数值",
            "entry_threshold",
            entry_threshold
        )


def _validate_arbitrage_params(params: Dict[str, Any]) -> None:
    """
    验证套利策略参数
    
    Args:
        params: 策略参数
        
    Raises:
        ValidationError: 验证失败时抛出
    """
    required_params = ['price_difference_threshold', 'max_position_size']
    
    for param in required_params:
        if param not in params:
            raise ValidationError(f"套利策略缺少参数: {param}", param)
    
    # 验证价差阈值
    price_diff_threshold = params['price_difference_threshold']
    if not isinstance(price_diff_threshold, (int, float)) or price_diff_threshold <= 0:
        raise ValidationError(
            "价差阈值必须是正数",
            "price_difference_threshold",
            price_diff_threshold
        )
    
    # 验证最大持仓
    max_position_size = params['max_position_size']
    if not isinstance(max_position_size, (int, float)) or max_position_size <= 0:
        raise ValidationError(
            "最大持仓必须是正数",
            "max_position_size",
            max_position_size
        )


def _validate_market_making_params(params: Dict[str, Any]) -> None:
    """
    验证做市策略参数
    
    Args:
        params: 策略参数
        
    Raises:
        ValidationError: 验证失败时抛出
    """
    required_params = ['spread_percentage', 'order_size']
    
    for param in required_params:
        if param not in params:
            raise ValidationError(f"做市策略缺少参数: {param}", param)
    
    # 验证价差百分比
    spread_percentage = params['spread_percentage']
    if not isinstance(spread_percentage, (int, float)) or spread_percentage <= 0:
        raise ValidationError(
            "价差百分比必须是正数",
            "spread_percentage",
            spread_percentage
        )
    
    # 验证订单大小
    order_size = params['order_size']
    if not isinstance(order_size, (int, float)) or order_size <= 0:
        raise ValidationError(
            "订单大小必须是正数",
            "order_size",
            order_size
        )


def _validate_risk_management_config(config: Dict[str, Any]) -> None:
    """
    验证风险管理配置
    
    Args:
        config: 风险管理配置
        
    Raises:
        ValidationError: 验证失败时抛出
    """
    if not isinstance(config, dict):
        raise ValidationError(
            "风险管理配置必须是字典类型",
            "risk_management",
            config
        )
    
    # 验证止损
    if 'stop_loss' in config:
        stop_loss = config['stop_loss']
        if not isinstance(stop_loss, (int, float)) or stop_loss <= 0 or stop_loss >= 1:
            raise ValidationError(
                "止损必须是0到1之间的数值",
                "stop_loss",
                stop_loss
            )
    
    # 验证止盈
    if 'take_profit' in config:
        take_profit = config['take_profit']
        if not isinstance(take_profit, (int, float)) or take_profit <= 0:
            raise ValidationError(
                "止盈必须是正数",
                "take_profit",
                take_profit
            )
    
    # 验证最大持仓
    if 'max_position_size' in config:
        max_position = config['max_position_size']
        if not isinstance(max_position, (int, float)) or max_position <= 0:
            raise ValidationError(
                "最大持仓必须是正数",
                "max_position_size",
                max_position
            )


def _validate_execution_config(config: Dict[str, Any]) -> None:
    """
    验证执行配置
    
    Args:
        config: 执行配置
        
    Raises:
        ValidationError: 验证失败时抛出
    """
    if not isinstance(config, dict):
        raise ValidationError(
            "执行配置必须是字典类型",
            "execution",
            config
        )
    
    # 验证订单类型
    if 'order_type' in config:
        order_type = config['order_type']
        valid_order_types = ['market', 'limit', 'stop', 'stop_limit']
        if order_type not in valid_order_types:
            raise ValidationError(
                f"无效的订单类型: {order_type}",
                "order_type",
                order_type
            )
    
    # 验证执行频率
    if 'frequency' in config:
        frequency = config['frequency']
        valid_frequencies = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
        if frequency not in valid_frequencies:
            raise ValidationError(
                f"无效的执行频率: {frequency}",
                "frequency",
                frequency
            )


def validate_backtest_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证回测参数
    
    Args:
        params: 回测参数字典
        
    Returns:
        Dict[str, Any]: 验证后的参数
        
    Raises:
        ValidationError: 验证失败时抛出
    """
    if not isinstance(params, dict):
        raise ValidationError("回测参数必须是字典类型", "params", params)
    
    # 必需字段
    required_fields = ['start_date', 'end_date', 'initial_capital']
    for field in required_fields:
        if field not in params:
            raise ValidationError(f"缺少必需字段: {field}", field)
    
    # 验证日期
    start_date = params['start_date']
    end_date = params['end_date']
    
    if isinstance(start_date, str):
        try:
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            raise ValidationError(
                "开始日期格式无效",
                "start_date",
                start_date
            )
    
    if isinstance(end_date, str):
        try:
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            raise ValidationError(
                "结束日期格式无效",
                "end_date",
                end_date
            )
    
    if start_date >= end_date:
        raise ValidationError(
            "开始日期必须早于结束日期",
            "start_date"
        )
    
    # 验证回测期间不能太长（最多5年）
    max_duration = timedelta(days=5 * 365)
    if end_date - start_date > max_duration:
        raise ValidationError(
            "回测期间不能超过5年",
            "end_date"
        )
    
    # 验证初始资金
    initial_capital = params['initial_capital']
    if not isinstance(initial_capital, (int, float, Decimal)) or initial_capital <= 0:
        raise ValidationError(
            "初始资金必须是正数",
            "initial_capital",
            initial_capital
        )
    
    # 验证可选参数
    if 'commission_rate' in params:
        commission_rate = params['commission_rate']
        if not isinstance(commission_rate, (int, float)) or commission_rate < 0 or commission_rate > 0.1:
            raise ValidationError(
                "手续费率必须是0到0.1之间的数值",
                "commission_rate",
                commission_rate
            )
    
    if 'slippage' in params:
        slippage = params['slippage']
        if not isinstance(slippage, (int, float)) or slippage < 0 or slippage > 0.01:
            raise ValidationError(
                "滑点必须是0到0.01之间的数值",
                "slippage",
                slippage
            )
    
    if 'benchmark' in params:
        benchmark = params['benchmark']
        if not isinstance(benchmark, str) or not benchmark.strip():
            raise ValidationError(
                "基准必须是非空字符串",
                "benchmark",
                benchmark
            )
    
    return params


def validate_risk_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证风险参数
    
    Args:
        params: 风险参数字典
        
    Returns:
        Dict[str, Any]: 验证后的参数
        
    Raises:
        ValidationError: 验证失败时抛出
    """
    if not isinstance(params, dict):
        raise ValidationError("风险参数必须是字典类型", "params", params)
    
    # 验证VaR置信度
    if 'var_confidence' in params:
        var_confidence = params['var_confidence']
        if not isinstance(var_confidence, (int, float)) or var_confidence <= 0 or var_confidence >= 1:
            raise ValidationError(
                "VaR置信度必须是0到1之间的数值",
                "var_confidence",
                var_confidence
            )
    
    # 验证最大回撤阈值
    if 'max_drawdown_threshold' in params:
        max_drawdown = params['max_drawdown_threshold']
        if not isinstance(max_drawdown, (int, float)) or max_drawdown <= 0 or max_drawdown >= 1:
            raise ValidationError(
                "最大回撤阈值必须是0到1之间的数值",
                "max_drawdown_threshold",
                max_drawdown
            )
    
    # 验证持仓限制
    if 'position_limit' in params:
        position_limit = params['position_limit']
        if not isinstance(position_limit, (int, float)) or position_limit <= 0:
            raise ValidationError(
                "持仓限制必须是正数",
                "position_limit",
                position_limit
            )
    
    # 验证日损失限制
    if 'daily_loss_limit' in params:
        daily_loss_limit = params['daily_loss_limit']
        if not isinstance(daily_loss_limit, (int, float)) or daily_loss_limit <= 0:
            raise ValidationError(
                "日损失限制必须是正数",
                "daily_loss_limit",
                daily_loss_limit
            )
    
    return params


def validate_symbol(symbol: str) -> str:
    """
    验证交易品种代码
    
    Args:
        symbol: 交易品种代码
        
    Returns:
        str: 验证后的代码
        
    Raises:
        ValidationError: 验证失败时抛出
    """
    if not symbol or not isinstance(symbol, str):
        raise ValidationError("交易品种代码不能为空", "symbol", symbol)
    
    # 移除空白字符并转换为大写
    symbol = symbol.strip().upper()
    
    # 验证格式（字母、数字、下划线、连字符）
    if not re.match(r'^[A-Z0-9_-]+$', symbol):
        raise ValidationError(
            "交易品种代码只能包含字母、数字、下划线和连字符",
            "symbol",
            symbol
        )
    
    # 验证长度
    if len(symbol) < 2 or len(symbol) > 20:
        raise ValidationError(
            "交易品种代码长度必须在2到20个字符之间",
            "symbol",
            symbol
        )
    
    return symbol


def validate_timeframe(timeframe: str) -> str:
    """
    验证时间框架
    
    Args:
        timeframe: 时间框架
        
    Returns:
        str: 验证后的时间框架
        
    Raises:
        ValidationError: 验证失败时抛出
    """
    if not timeframe or not isinstance(timeframe, str):
        raise ValidationError("时间框架不能为空", "timeframe", timeframe)
    
    timeframe = timeframe.strip().lower()
    
    valid_timeframes = [
        '1m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '1w', '1M'
    ]
    
    if timeframe not in valid_timeframes:
        raise ValidationError(
            f"无效的时间框架: {timeframe}",
            "timeframe",
            timeframe
        )
    
    return timeframe


def validate_pagination_params(page: int, size: int, max_size: int = 100) -> tuple:
    """
    验证分页参数
    
    Args:
        page: 页码
        size: 每页大小
        max_size: 最大每页大小
        
    Returns:
        tuple: (page, size)
        
    Raises:
        ValidationError: 验证失败时抛出
    """
    if not isinstance(page, int) or page < 1:
        raise ValidationError("页码必须是大于0的整数", "page", page)
    
    if not isinstance(size, int) or size < 1:
        raise ValidationError("每页大小必须是大于0的整数", "size", size)
    
    if size > max_size:
        raise ValidationError(
            f"每页大小不能超过{max_size}",
            "size",
            size
        )
    
    return page, size