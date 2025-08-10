#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 交易所API路由

提供统一的交易所接口，支持多交易所
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field

from ..services.exchange_service import get_exchange_service, ExchangeService
from ..core.security import get_current_user
from ..schemas.user import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/exchanges", tags=["交易所"])


# ==================== 请求/响应模型 ====================

class ExchangeConnectionRequest(BaseModel):
    """交易所连接请求模型"""
    api_key: str = Field(..., description="API密钥")
    api_secret: str = Field(..., description="API密钥")
    testnet: bool = Field(default=False, description="是否使用测试网")


class MarketTickerResponse(BaseModel):
    """市场行情响应模型"""
    symbol: str = Field(..., description="交易对符号")
    price: float = Field(..., description="最新价格")
    bid_price: Optional[float] = Field(None, description="买一价")
    ask_price: Optional[float] = Field(None, description="卖一价")
    volume_24h: Optional[float] = Field(None, description="24小时成交量")
    quote_volume_24h: Optional[float] = Field(None, description="24小时成交额")
    price_change_24h: Optional[float] = Field(None, description="24小时价格变化百分比")
    high_24h: Optional[float] = Field(None, description="24小时最高价")
    low_24h: Optional[float] = Field(None, description="24小时最低价")
    timestamp: str = Field(..., description="时间戳")


class OrderBookResponse(BaseModel):
    """订单簿响应模型"""
    symbol: str = Field(..., description="交易对符号")
    market_type: str = Field(..., description="市场类型")
    bids: List[List[float]] = Field(..., description="买单列表")
    asks: List[List[float]] = Field(..., description="卖单列表")
    timestamp: str = Field(..., description="时间戳")


class TradeResponse(BaseModel):
    """成交记录响应模型"""
    id: str = Field(..., description="成交ID")
    price: float = Field(..., description="成交价格")
    amount: float = Field(..., description="成交数量")
    side: str = Field(..., description="买卖方向")
    timestamp: str = Field(..., description="成交时间")


class KlineResponse(BaseModel):
    """K线数据响应模型"""
    timestamp: int = Field(..., description="时间戳")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: float = Field(..., description="成交量")
    quote_volume: Optional[float] = Field(None, description="成交额")


class AccountBalanceResponse(BaseModel):
    """账户余额响应模型"""
    currency: str = Field(..., description="币种")
    available: float = Field(..., description="可用余额")
    locked: float = Field(..., description="冻结余额")
    total: float = Field(..., description="总余额")


class PositionResponse(BaseModel):
    """持仓响应模型"""
    contract: str = Field(..., description="合约名称")
    size: float = Field(..., description="持仓数量")
    margin: float = Field(..., description="保证金")
    entry_price: float = Field(..., description="开仓价格")
    mark_price: float = Field(..., description="标记价格")
    unrealized_pnl: float = Field(..., description="未实现盈亏")
    realized_pnl: float = Field(..., description="已实现盈亏")
    leverage: float = Field(..., description="杠杆倍数")
    side: str = Field(..., description="持仓方向")
    timestamp: str = Field(..., description="时间戳")


class CreateOrderRequest(BaseModel):
    """创建订单请求模型"""
    symbol: str = Field(..., description="交易对/合约符号")
    side: str = Field(..., description="买卖方向 (buy/sell)")
    type: str = Field(..., description="订单类型 (limit/market)")
    amount: float = Field(..., description="数量")
    price: Optional[float] = Field(None, description="价格（限价单必填）")
    market_type: str = Field(default="spot", description="市场类型 (spot/futures)")
    time_in_force: str = Field(default="gtc", description="时效性")
    reduce_only: bool = Field(default=False, description="只减仓（期货）")
    post_only: bool = Field(default=False, description="只做maker")
    client_order_id: Optional[str] = Field(None, description="客户端订单ID")


class OrderResponse(BaseModel):
    """订单响应模型"""
    order_id: str = Field(..., description="订单ID")
    client_order_id: Optional[str] = Field(None, description="客户端订单ID")
    symbol: str = Field(..., description="交易对符号")
    side: str = Field(..., description="买卖方向")
    type: str = Field(..., description="订单类型")
    amount: float = Field(..., description="订单数量")
    price: float = Field(..., description="订单价格")
    status: str = Field(..., description="订单状态")
    filled_amount: float = Field(..., description="已成交数量")
    remaining_amount: float = Field(..., description="剩余数量")
    average_price: Optional[float] = Field(None, description="平均成交价")
    create_time: str = Field(..., description="创建时间")
    update_time: Optional[str] = Field(None, description="更新时间")
    market_type: str = Field(..., description="市场类型")


# ==================== 交易所管理接口 ====================

@router.get("/available", summary="获取可用交易所列表")
async def get_available_exchanges(
    exchange_service: ExchangeService = Depends(get_exchange_service)
) -> List[Dict[str, Any]]:
    """
    获取可用交易所列表
    
    Returns:
        交易所列表
    """
    try:
        return await exchange_service.get_available_exchanges()
    except Exception as e:
        logger.error(f"获取可用交易所列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取可用交易所列表失败: {str(e)}")


@router.get("/{exchange_name}/info", summary="获取交易所信息")
async def get_exchange_info(
    exchange_name: str,
    exchange_service: ExchangeService = Depends(get_exchange_service)
) -> Dict[str, Any]:
    """
    获取指定交易所信息
    
    Args:
        exchange_name: 交易所名称
        
    Returns:
        交易所信息
    """
    try:
        return await exchange_service.get_exchange_info(exchange_name)
    except Exception as e:
        logger.error(f"获取交易所信息失败 {exchange_name}: {e}")
        raise HTTPException(status_code=500, detail=f"获取交易所信息失败: {str(e)}")


@router.post("/{exchange_name}/connect", summary="连接交易所")
async def connect_exchange(
    exchange_name: str,
    connection_request: ExchangeConnectionRequest,
    current_user: UserResponse = Depends(get_current_user),
    exchange_service: ExchangeService = Depends(get_exchange_service)
) -> Dict[str, Any]:
    """
    连接指定交易所
    
    Args:
        exchange_name: 交易所名称
        connection_request: 连接请求
        
    Returns:
        连接结果
    """
    try:
        return await exchange_service.connect_exchange(
            exchange_name,
            connection_request.api_key,
            connection_request.api_secret,
            connection_request.testnet
        )
    except Exception as e:
        logger.error(f"连接交易所失败 {exchange_name}: {e}")
        raise HTTPException(status_code=500, detail=f"连接交易所失败: {str(e)}")


@router.post("/{exchange_name}/disconnect", summary="断开交易所连接")
async def disconnect_exchange(
    exchange_name: str,
    current_user: UserResponse = Depends(get_current_user),
    exchange_service: ExchangeService = Depends(get_exchange_service)
) -> Dict[str, Any]:
    """
    断开指定交易所连接
    
    Args:
        exchange_name: 交易所名称
        
    Returns:
        断开结果
    """
    try:
        return await exchange_service.disconnect_exchange(exchange_name)
    except Exception as e:
        logger.error(f"断开交易所连接失败 {exchange_name}: {e}")
        raise HTTPException(status_code=500, detail=f"断开交易所连接失败: {str(e)}")


# ==================== 市场数据接口 ====================

@router.get("/{exchange_name}/symbols", summary="获取交易对列表")
async def get_symbols(
    exchange_name: str,
    market_type: str = Query(default="spot", description="市场类型 (spot/futures)"),
    exchange_service: ExchangeService = Depends(get_exchange_service)
) -> List[Dict[str, Any]]:
    """
    获取指定交易所的交易对列表
    
    Args:
        exchange_name: 交易所名称
        market_type: 市场类型 (spot/futures)
        
    Returns:
        交易对列表
    """
    try:
        return await exchange_service.get_symbols(exchange_name, market_type)
    except Exception as e:
        logger.error(f"获取交易对列表失败 {exchange_name}: {e}")
        raise HTTPException(status_code=500, detail=f"获取交易对列表失败: {str(e)}")


@router.get("/{exchange_name}/ticker/{symbol}", response_model=MarketTickerResponse, summary="获取行情数据")
async def get_ticker(
    exchange_name: str,
    symbol: str,
    market_type: str = Query(default="spot", description="市场类型 (spot/futures)"),
    exchange_service: ExchangeService = Depends(get_exchange_service)
) -> MarketTickerResponse:
    """
    获取指定交易对的行情数据
    
    Args:
        exchange_name: 交易所名称
        symbol: 交易对符号，如 BTC_USDT
        market_type: 市场类型 (spot/futures)
        
    Returns:
        行情数据
    """
    try:
        ticker_data = await exchange_service.get_ticker(exchange_name, symbol, market_type)
        
        if not ticker_data:
            raise HTTPException(status_code=404, detail=f"未找到交易对 {symbol} 的行情数据")
        
        return MarketTickerResponse(**ticker_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取行情数据失败 {exchange_name}/{symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"获取行情数据失败: {str(e)}")


@router.get("/{exchange_name}/tickers", response_model=List[MarketTickerResponse], summary="获取所有行情数据")
async def get_tickers(
    exchange_name: str,
    market_type: str = Query(default="spot", description="市场类型 (spot/futures)"),
    exchange_service: ExchangeService = Depends(get_exchange_service)
) -> List[MarketTickerResponse]:
    """
    获取指定交易所的所有行情数据
    
    Args:
        exchange_name: 交易所名称
        market_type: 市场类型 (spot/futures)
        
    Returns:
        行情数据列表
    """
    try:
        tickers_data = await exchange_service.get_tickers(exchange_name, market_type)
        return [MarketTickerResponse(**ticker) for ticker in tickers_data]
        
    except Exception as e:
        logger.error(f"获取所有行情数据失败 {exchange_name}: {e}")
        raise HTTPException(status_code=500, detail=f"获取所有行情数据失败: {str(e)}")


@router.get("/{exchange_name}/orderbook/{symbol}", response_model=OrderBookResponse, summary="获取订单簿")
async def get_order_book(
    exchange_name: str,
    symbol: str,
    market_type: str = Query(default="spot", description="市场类型 (spot/futures)"),
    limit: int = Query(default=20, ge=1, le=100, description="深度限制"),
    exchange_service: ExchangeService = Depends(get_exchange_service)
) -> OrderBookResponse:
    """
    获取指定交易对的订单簿数据
    
    Args:
        exchange_name: 交易所名称
        symbol: 交易对符号
        market_type: 市场类型 (spot/futures)
        limit: 深度限制
        
    Returns:
        订单簿数据
    """
    try:
        order_book_data = await exchange_service.get_order_book(exchange_name, symbol, market_type, limit)
        return OrderBookResponse(**order_book_data)
        
    except Exception as e:
        logger.error(f"获取订单簿失败 {exchange_name}/{symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"获取订单簿失败: {str(e)}")


@router.get("/{exchange_name}/trades/{symbol}", response_model=List[TradeResponse], summary="获取成交记录")
async def get_recent_trades(
    exchange_name: str,
    symbol: str,
    market_type: str = Query(default="spot", description="市场类型 (spot/futures)"),
    limit: int = Query(default=100, ge=1, le=500, description="记录数量限制"),
    exchange_service: ExchangeService = Depends(get_exchange_service)
) -> List[TradeResponse]:
    """
    获取指定交易对的最近成交记录
    
    Args:
        exchange_name: 交易所名称
        symbol: 交易对符号
        market_type: 市场类型 (spot/futures)
        limit: 记录数量限制
        
    Returns:
        成交记录列表
    """
    try:
        trades_data = await exchange_service.get_trades(exchange_name, symbol, market_type, limit)
        return [TradeResponse(**trade) for trade in trades_data]
        
    except Exception as e:
        logger.error(f"获取成交记录失败 {exchange_name}/{symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"获取成交记录失败: {str(e)}")


@router.get("/{exchange_name}/klines/{symbol}", response_model=List[KlineResponse], summary="获取K线数据")
async def get_klines(
    exchange_name: str,
    symbol: str,
    interval: str = Query(default="1m", description="时间间隔"),
    market_type: str = Query(default="spot", description="市场类型 (spot/futures)"),
    limit: int = Query(default=100, ge=1, le=1000, description="数量限制"),
    start_time: Optional[int] = Query(None, description="开始时间戳"),
    end_time: Optional[int] = Query(None, description="结束时间戳"),
    exchange_service: ExchangeService = Depends(get_exchange_service)
) -> List[KlineResponse]:
    """
    获取指定交易对的K线数据
    
    Args:
        exchange_name: 交易所名称
        symbol: 交易对符号
        interval: 时间间隔
        market_type: 市场类型 (spot/futures)
        limit: 数量限制
        start_time: 开始时间戳
        end_time: 结束时间戳
        
    Returns:
        K线数据列表
    """
    try:
        klines_data = await exchange_service.get_klines(
            exchange_name, symbol, interval, market_type, limit, start_time, end_time
        )
        return [KlineResponse(**kline) for kline in klines_data]
        
    except Exception as e:
        logger.error(f"获取K线数据失败 {exchange_name}/{symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"获取K线数据失败: {str(e)}")


# ==================== 账户管理接口 ====================

@router.get("/{exchange_name}/account", summary="获取账户信息")
async def get_account_info(
    exchange_name: str,
    market_type: str = Query(default="spot", description="市场类型 (spot/futures)"),
    current_user: UserResponse = Depends(get_current_user),
    exchange_service: ExchangeService = Depends(get_exchange_service)
) -> Dict[str, Any]:
    """
    获取当前用户的账户信息
    
    Args:
        exchange_name: 交易所名称
        market_type: 市场类型 (spot/futures)
        
    Returns:
        账户信息
    """
    try:
        return await exchange_service.get_account_info(exchange_name, market_type)
        
    except Exception as e:
        logger.error(f"获取账户信息失败 {exchange_name}: {e}")
        raise HTTPException(status_code=500, detail=f"获取账户信息失败: {str(e)}")


@router.get("/{exchange_name}/balances", response_model=List[AccountBalanceResponse], summary="获取账户余额")
async def get_account_balances(
    exchange_name: str,
    market_type: str = Query(default="spot", description="市场类型 (spot/futures)"),
    current_user: UserResponse = Depends(get_current_user),
    exchange_service: ExchangeService = Depends(get_exchange_service)
) -> List[AccountBalanceResponse]:
    """
    获取当前用户的账户余额
    
    Args:
        exchange_name: 交易所名称
        market_type: 市场类型 (spot/futures)
        
    Returns:
        账户余额列表
    """
    try:
        balances_data = await exchange_service.get_balances(exchange_name, market_type)
        return [AccountBalanceResponse(**balance) for balance in balances_data]
        
    except Exception as e:
        logger.error(f"获取账户余额失败 {exchange_name}: {e}")
        raise HTTPException(status_code=500, detail=f"获取账户余额失败: {str(e)}")


@router.get("/{exchange_name}/positions", response_model=List[PositionResponse], summary="获取持仓信息")
async def get_positions(
    exchange_name: str,
    settle: str = Query(default="usdt", description="结算货币"),
    current_user: UserResponse = Depends(get_current_user),
    exchange_service: ExchangeService = Depends(get_exchange_service)
) -> List[PositionResponse]:
    """
    获取当前用户的期货持仓信息
    
    Args:
        exchange_name: 交易所名称
        settle: 结算货币
        
    Returns:
        持仓信息列表
    """
    try:
        positions_data = await exchange_service.get_positions(exchange_name, settle)
        return [PositionResponse(**position) for position in positions_data]
        
    except Exception as e:
        logger.error(f"获取持仓信息失败 {exchange_name}: {e}")
        raise HTTPException(status_code=500, detail=f"获取持仓信息失败: {str(e)}")


# ==================== 交易执行接口 ====================

@router.post("/{exchange_name}/orders", response_model=OrderResponse, summary="创建订单")
async def create_order(
    exchange_name: str,
    order_request: CreateOrderRequest,
    current_user: UserResponse = Depends(get_current_user),
    exchange_service: ExchangeService = Depends(get_exchange_service)
) -> OrderResponse:
    """
    创建新订单
    
    Args:
        exchange_name: 交易所名称
        order_request: 订单创建请求
        
    Returns:
        订单信息
    """
    try:
        order_data = await exchange_service.create_order(
            exchange_name=exchange_name,
            symbol=order_request.symbol,
            side=order_request.side,
            order_type=order_request.type,
            amount=order_request.amount,
            price=order_request.price,
            market_type=order_request.market_type,
            time_in_force=order_request.time_in_force,
            reduce_only=order_request.reduce_only,
            post_only=order_request.post_only,
            client_order_id=order_request.client_order_id
        )
        
        return OrderResponse(**order_data)
        
    except Exception as e:
        logger.error(f"创建订单失败 {exchange_name}: {e}")
        raise HTTPException(status_code=500, detail=f"创建订单失败: {str(e)}")


@router.delete("/{exchange_name}/orders/{order_id}", summary="取消订单")
async def cancel_order(
    exchange_name: str,
    order_id: str,
    symbol: str = Query(..., description="交易对符号"),
    market_type: str = Query(default="spot", description="市场类型 (spot/futures)"),
    current_user: UserResponse = Depends(get_current_user),
    exchange_service: ExchangeService = Depends(get_exchange_service)
) -> Dict[str, Any]:
    """
    取消指定订单
    
    Args:
        exchange_name: 交易所名称
        order_id: 订单ID
        symbol: 交易对符号
        market_type: 市场类型 (spot/futures)
        
    Returns:
        取消结果
    """
    try:
        result = await exchange_service.cancel_order(exchange_name, order_id, symbol, market_type)
        return result
        
    except Exception as e:
        logger.error(f"取消订单失败 {exchange_name}/{order_id}: {e}")
        raise HTTPException(status_code=500, detail=f"取消订单失败: {str(e)}")


@router.get("/{exchange_name}/orders/{order_id}", response_model=OrderResponse, summary="获取订单详情")
async def get_order(
    exchange_name: str,
    order_id: str,
    symbol: str = Query(..., description="交易对符号"),
    market_type: str = Query(default="spot", description="市场类型 (spot/futures)"),
    current_user: UserResponse = Depends(get_current_user),
    exchange_service: ExchangeService = Depends(get_exchange_service)
) -> OrderResponse:
    """
    获取指定订单的详细信息
    
    Args:
        exchange_name: 交易所名称
        order_id: 订单ID
        symbol: 交易对符号
        market_type: 市场类型 (spot/futures)
        
    Returns:
        订单详情
    """
    try:
        order_data = await exchange_service.get_order(exchange_name, order_id, symbol, market_type)
        return OrderResponse(**order_data)
        
    except Exception as e:
        logger.error(f"获取订单详情失败 {exchange_name}/{order_id}: {e}")
        raise HTTPException(status_code=500, detail=f"获取订单详情失败: {str(e)}")


@router.get("/{exchange_name}/orders/open", response_model=List[OrderResponse], summary="获取未成交订单")
async def get_open_orders(
    exchange_name: str,
    symbol: Optional[str] = Query(None, description="交易对符号（可选）"),
    market_type: str = Query(default="spot", description="市场类型 (spot/futures)"),
    current_user: UserResponse = Depends(get_current_user),
    exchange_service: ExchangeService = Depends(get_exchange_service)
) -> List[OrderResponse]:
    """
    获取未成交订单列表
    
    Args:
        exchange_name: 交易所名称
        symbol: 交易对符号（可选）
        market_type: 市场类型 (spot/futures)
        
    Returns:
        订单列表
    """
    try:
        orders_data = await exchange_service.get_open_orders(exchange_name, symbol, market_type)
        return [OrderResponse(**order) for order in orders_data]
        
    except Exception as e:
        logger.error(f"获取未成交订单失败 {exchange_name}: {e}")
        raise HTTPException(status_code=500, detail=f"获取未成交订单失败: {str(e)}")


@router.get("/{exchange_name}/orders/history", response_model=List[OrderResponse], summary="获取历史订单")
async def get_order_history(
    exchange_name: str,
    symbol: Optional[str] = Query(None, description="交易对符号（可选）"),
    market_type: str = Query(default="spot", description="市场类型 (spot/futures)"),
    limit: int = Query(default=100, ge=1, le=500, description="数量限制"),
    current_user: UserResponse = Depends(get_current_user),
    exchange_service: ExchangeService = Depends(get_exchange_service)
) -> List[OrderResponse]:
    """
    获取历史订单列表
    
    Args:
        exchange_name: 交易所名称
        symbol: 交易对符号（可选）
        market_type: 市场类型 (spot/futures)
        limit: 数量限制
        
    Returns:
        订单列表
    """
    try:
        orders_data = await exchange_service.get_order_history(exchange_name, symbol, market_type, limit)
        return [OrderResponse(**order) for order in orders_data]
        
    except Exception as e:
        logger.error(f"获取历史订单失败 {exchange_name}: {e}")
        raise HTTPException(status_code=500, detail=f"获取历史订单失败: {str(e)}")