#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 市场数据模型

定义市场数据相关的数据库模型
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

from ..core.database import Base

logger = logging.getLogger(__name__)


class MarketTicker(Base):
    """市场行情数据模型"""
    __tablename__ = "market_tickers"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), nullable=False, index=True, comment="交易对符号")
    market_type = Column(String(20), nullable=False, default="spot", comment="市场类型")
    
    # 价格信息
    last_price = Column(Float, nullable=False, comment="最新价格")
    bid_price = Column(Float, comment="买一价")
    ask_price = Column(Float, comment="卖一价")
    high_24h = Column(Float, comment="24小时最高价")
    low_24h = Column(Float, comment="24小时最低价")
    open_24h = Column(Float, comment="24小时开盘价")
    
    # 成交量信息
    volume_24h = Column(Float, comment="24小时成交量")
    volume_24h_quote = Column(Float, comment="24小时成交额")
    
    # 变化信息
    change_24h = Column(Float, comment="24小时价格变化")
    change_percentage_24h = Column(Float, comment="24小时价格变化百分比")
    
    # 时间戳
    timestamp = Column(Integer, nullable=False, comment="数据时间戳")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 索引
    __table_args__ = (
        Index('idx_tickers_symbol_market_timestamp', 'symbol', 'market_type', 'timestamp'),
        Index('idx_tickers_timestamp', 'timestamp'),
    )


class MarketOrderBook(Base):
    """订单簿数据模型"""
    __tablename__ = "market_orderbooks"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), nullable=False, index=True, comment="交易对符号")
    market_type = Column(String(20), nullable=False, default="spot", comment="市场类型")
    
    # 订单簿数据
    bids = Column(Text, comment="买单数据 (JSON格式)")
    asks = Column(Text, comment="卖单数据 (JSON格式)")
    
    # 时间戳
    timestamp = Column(Integer, nullable=False, comment="数据时间戳")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    
    # 索引
    __table_args__ = (
        Index('idx_orderbooks_symbol_market_timestamp', 'symbol', 'market_type', 'timestamp'),
    )


class MarketTrade(Base):
    """成交记录数据模型"""
    __tablename__ = "market_trades"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), nullable=False, index=True, comment="交易对符号")
    market_type = Column(String(20), nullable=False, default="spot", comment="市场类型")
    trade_id = Column(String(100), nullable=False, comment="交易ID")
    
    # 交易信息
    price = Column(Float, nullable=False, comment="成交价格")
    amount = Column(Float, nullable=False, comment="成交数量")
    side = Column(String(10), nullable=False, comment="交易方向 (buy/sell)")
    
    # 时间戳
    timestamp = Column(Integer, nullable=False, comment="成交时间戳")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    
    # 索引
    __table_args__ = (
        Index('idx_trades_symbol_market_timestamp', 'symbol', 'market_type', 'timestamp'),
        Index('idx_trades_trade_id', 'trade_id'),
    )


class MarketKline(Base):
    """K线数据模型"""
    __tablename__ = "market_klines"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), nullable=False, index=True, comment="交易对符号")
    market_type = Column(String(20), nullable=False, default="spot", comment="市场类型")
    interval = Column(String(10), nullable=False, comment="K线间隔")
    
    # OHLCV数据
    open_time = Column(Integer, nullable=False, comment="开盘时间戳")
    close_time = Column(Integer, nullable=False, comment="收盘时间戳")
    open_price = Column(Float, nullable=False, comment="开盘价")
    high_price = Column(Float, nullable=False, comment="最高价")
    low_price = Column(Float, nullable=False, comment="最低价")
    close_price = Column(Float, nullable=False, comment="收盘价")
    volume = Column(Float, nullable=False, comment="成交量")
    quote_volume = Column(Float, comment="成交额")
    
    # 统计信息
    trade_count = Column(Integer, comment="成交笔数")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 索引
    __table_args__ = (
        Index('idx_symbol_market_interval_time', 'symbol', 'market_type', 'interval', 'open_time'),
        Index('idx_open_time', 'open_time'),
    )


class TradingPair(Base):
    """交易对信息模型"""
    __tablename__ = "trading_pairs"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), nullable=False, unique=True, index=True, comment="交易对符号")
    market_type = Column(String(20), nullable=False, default="spot", comment="市场类型")
    
    # 交易对信息
    base_currency = Column(String(20), nullable=False, comment="基础货币")
    quote_currency = Column(String(20), nullable=False, comment="计价货币")
    
    # 交易规则
    min_amount = Column(Float, comment="最小交易数量")
    max_amount = Column(Float, comment="最大交易数量")
    amount_precision = Column(Integer, comment="数量精度")
    price_precision = Column(Integer, comment="价格精度")
    
    # 费率信息
    maker_fee = Column(Float, comment="挂单手续费")
    taker_fee = Column(Float, comment="吃单手续费")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否活跃")
    is_trading_enabled = Column(Boolean, default=True, comment="是否允许交易")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 索引
    __table_args__ = (
        Index('idx_base_quote', 'base_currency', 'quote_currency'),
        Index('idx_market_type', 'market_type'),
    )


class MarketStats(Base):
    """市场统计数据模型"""
    __tablename__ = "market_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), nullable=False, index=True, comment="交易对符号")
    market_type = Column(String(20), nullable=False, default="spot", comment="市场类型")
    
    # 统计周期
    period = Column(String(10), nullable=False, comment="统计周期 (1h/4h/1d/1w)")
    period_start = Column(Integer, nullable=False, comment="周期开始时间戳")
    period_end = Column(Integer, nullable=False, comment="周期结束时间戳")
    
    # 价格统计
    open_price = Column(Float, comment="开盘价")
    close_price = Column(Float, comment="收盘价")
    high_price = Column(Float, comment="最高价")
    low_price = Column(Float, comment="最低价")
    avg_price = Column(Float, comment="平均价")
    
    # 成交统计
    total_volume = Column(Float, comment="总成交量")
    total_quote_volume = Column(Float, comment="总成交额")
    trade_count = Column(Integer, comment="成交笔数")
    
    # 价格变化
    price_change = Column(Float, comment="价格变化")
    price_change_percent = Column(Float, comment="价格变化百分比")
    
    # 波动率
    volatility = Column(Float, comment="价格波动率")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 索引
    __table_args__ = (
        Index('idx_symbol_market_period_start', 'symbol', 'market_type', 'period', 'period_start'),
        Index('idx_period_start', 'period_start'),
    )