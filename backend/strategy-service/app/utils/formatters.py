#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
格式化工具

提供各种数据格式化功能。
"""

import logging
from typing import Union, Optional
from decimal import Decimal
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def format_currency(
    amount: Union[int, float, Decimal],
    currency: str = "USD",
    decimal_places: int = 2,
    show_symbol: bool = True
) -> str:
    """
    格式化货币金额
    
    Args:
        amount: 金额
        currency: 货币代码
        decimal_places: 小数位数
        show_symbol: 是否显示货币符号
        
    Returns:
        str: 格式化后的货币字符串
    """
    try:
        # 货币符号映射
        currency_symbols = {
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
            "JPY": "¥",
            "CNY": "¥",
            "KRW": "₩",
            "BTC": "₿",
            "ETH": "Ξ"
        }
        
        # 转换为Decimal以确保精度
        if isinstance(amount, (int, float)):
            amount = Decimal(str(amount))
        
        # 格式化数字
        format_str = f"{{:,.{decimal_places}f}}"
        formatted_amount = format_str.format(float(amount))
        
        # 添加货币符号
        if show_symbol:
            symbol = currency_symbols.get(currency.upper(), currency.upper())
            if currency.upper() in ["USD", "EUR", "GBP", "CNY", "BTC", "ETH"]:
                return f"{symbol}{formatted_amount}"
            else:
                return f"{formatted_amount} {symbol}"
        
        return formatted_amount
        
    except Exception as e:
        logger.warning(f"格式化货币失败: {e}")
        return str(amount)


def format_percentage(
    value: Union[int, float, Decimal],
    decimal_places: int = 2,
    show_sign: bool = True,
    multiply_by_100: bool = True
) -> str:
    """
    格式化百分比
    
    Args:
        value: 数值（如果multiply_by_100为True，则为小数形式）
        decimal_places: 小数位数
        show_sign: 是否显示正负号
        multiply_by_100: 是否乘以100
        
    Returns:
        str: 格式化后的百分比字符串
    """
    try:
        # 转换为Decimal以确保精度
        if isinstance(value, (int, float)):
            value = Decimal(str(value))
        
        # 如果需要，乘以100
        if multiply_by_100:
            value = value * 100
        
        # 格式化数字
        format_str = f"{{:+.{decimal_places}f}}" if show_sign else f"{{:.{decimal_places}f}}"
        formatted_value = format_str.format(float(value))
        
        return f"{formatted_value}%"
        
    except Exception as e:
        logger.warning(f"格式化百分比失败: {e}")
        return f"{value}%"


def format_number(
    value: Union[int, float, Decimal],
    decimal_places: int = 2,
    use_thousands_separator: bool = True,
    scientific_notation: bool = False,
    scientific_threshold: float = 1e6
) -> str:
    """
    格式化数字
    
    Args:
        value: 数值
        decimal_places: 小数位数
        use_thousands_separator: 是否使用千位分隔符
        scientific_notation: 是否使用科学计数法
        scientific_threshold: 科学计数法阈值
        
    Returns:
        str: 格式化后的数字字符串
    """
    try:
        # 转换为float进行处理
        float_value = float(value)
        
        # 检查是否使用科学计数法
        if scientific_notation or abs(float_value) >= scientific_threshold:
            return f"{float_value:.{decimal_places}e}"
        
        # 格式化数字
        if use_thousands_separator:
            format_str = f"{{:,.{decimal_places}f}}"
        else:
            format_str = f"{{:.{decimal_places}f}}"
        
        return format_str.format(float_value)
        
    except Exception as e:
        logger.warning(f"格式化数字失败: {e}")
        return str(value)


def format_duration(
    duration: Union[timedelta, int, float],
    precision: str = "auto",
    show_milliseconds: bool = False
) -> str:
    """
    格式化时间间隔
    
    Args:
        duration: 时间间隔（timedelta对象或秒数）
        precision: 精度（"auto", "days", "hours", "minutes", "seconds"）
        show_milliseconds: 是否显示毫秒
        
    Returns:
        str: 格式化后的时间间隔字符串
    """
    try:
        # 转换为timedelta对象
        if isinstance(duration, (int, float)):
            duration = timedelta(seconds=duration)
        
        total_seconds = duration.total_seconds()
        
        # 计算各个时间单位
        days = int(total_seconds // 86400)
        hours = int((total_seconds % 86400) // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        milliseconds = int((total_seconds % 1) * 1000)
        
        # 根据精度格式化
        if precision == "auto":
            if days > 0:
                precision = "days"
            elif hours > 0:
                precision = "hours"
            elif minutes > 0:
                precision = "minutes"
            else:
                precision = "seconds"
        
        parts = []
        
        if precision in ["days", "hours", "minutes", "seconds"] and days > 0:
            parts.append(f"{days}天")
        
        if precision in ["hours", "minutes", "seconds"] and (hours > 0 or days > 0):
            parts.append(f"{hours}小时")
        
        if precision in ["minutes", "seconds"] and (minutes > 0 or hours > 0 or days > 0):
            parts.append(f"{minutes}分钟")
        
        if precision == "seconds" or (not parts and seconds > 0):
            if show_milliseconds and milliseconds > 0:
                parts.append(f"{seconds}.{milliseconds:03d}秒")
            else:
                parts.append(f"{seconds}秒")
        
        if not parts:
            if show_milliseconds:
                return f"{milliseconds}毫秒"
            else:
                return "0秒"
        
        return " ".join(parts)
        
    except Exception as e:
        logger.warning(f"格式化时间间隔失败: {e}")
        return str(duration)


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        str: 格式化后的文件大小字符串
    """
    try:
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        if i == 0:
            return f"{int(size)} {size_names[i]}"
        else:
            return f"{size:.1f} {size_names[i]}"
            
    except Exception as e:
        logger.warning(f"格式化文件大小失败: {e}")
        return f"{size_bytes} B"


def format_ratio(
    numerator: Union[int, float, Decimal],
    denominator: Union[int, float, Decimal],
    decimal_places: int = 2,
    handle_zero_denominator: str = "N/A"
) -> str:
    """
    格式化比率
    
    Args:
        numerator: 分子
        denominator: 分母
        decimal_places: 小数位数
        handle_zero_denominator: 分母为零时的处理方式
        
    Returns:
        str: 格式化后的比率字符串
    """
    try:
        if denominator == 0:
            return handle_zero_denominator
        
        ratio = float(numerator) / float(denominator)
        return f"{ratio:.{decimal_places}f}"
        
    except Exception as e:
        logger.warning(f"格式化比率失败: {e}")
        return handle_zero_denominator


def format_sharpe_ratio(
    returns: Union[int, float, Decimal],
    risk_free_rate: Union[int, float, Decimal],
    volatility: Union[int, float, Decimal],
    decimal_places: int = 3
) -> str:
    """
    格式化夏普比率
    
    Args:
        returns: 收益率
        risk_free_rate: 无风险利率
        volatility: 波动率
        decimal_places: 小数位数
        
    Returns:
        str: 格式化后的夏普比率字符串
    """
    try:
        if volatility == 0:
            return "N/A"
        
        excess_return = float(returns) - float(risk_free_rate)
        sharpe_ratio = excess_return / float(volatility)
        
        return f"{sharpe_ratio:.{decimal_places}f}"
        
    except Exception as e:
        logger.warning(f"格式化夏普比率失败: {e}")
        return "N/A"


def format_datetime_range(
    start_date: datetime,
    end_date: datetime,
    date_format: str = "%Y-%m-%d",
    include_time: bool = False
) -> str:
    """
    格式化日期时间范围
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        date_format: 日期格式
        include_time: 是否包含时间
        
    Returns:
        str: 格式化后的日期时间范围字符串
    """
    try:
        if include_time:
            format_str = f"{date_format} %H:%M:%S"
        else:
            format_str = date_format
        
        start_str = start_date.strftime(format_str)
        end_str = end_date.strftime(format_str)
        
        return f"{start_str} ~ {end_str}"
        
    except Exception as e:
        logger.warning(f"格式化日期时间范围失败: {e}")
        return f"{start_date} ~ {end_date}"


def format_trade_side(side: str) -> str:
    """
    格式化交易方向
    
    Args:
        side: 交易方向（"buy", "sell", "long", "short"等）
        
    Returns:
        str: 格式化后的交易方向字符串
    """
    side_mapping = {
        "buy": "买入",
        "sell": "卖出",
        "long": "做多",
        "short": "做空",
        "open": "开仓",
        "close": "平仓"
    }
    
    return side_mapping.get(side.lower(), side)


def format_order_status(status: str) -> str:
    """
    格式化订单状态
    
    Args:
        status: 订单状态
        
    Returns:
        str: 格式化后的订单状态字符串
    """
    status_mapping = {
        "pending": "待成交",
        "filled": "已成交",
        "partially_filled": "部分成交",
        "cancelled": "已取消",
        "rejected": "已拒绝",
        "expired": "已过期"
    }
    
    return status_mapping.get(status.lower(), status)


def format_strategy_status(status: str) -> str:
    """
    格式化策略状态
    
    Args:
        status: 策略状态
        
    Returns:
        str: 格式化后的策略状态字符串
    """
    status_mapping = {
        "draft": "草稿",
        "active": "运行中",
        "paused": "已暂停",
        "stopped": "已停止",
        "error": "错误",
        "backtesting": "回测中"
    }
    
    return status_mapping.get(status.lower(), status)


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    截断字符串
    
    Args:
        text: 原始字符串
        max_length: 最大长度
        suffix: 截断后缀
        
    Returns:
        str: 截断后的字符串
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix