#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - Gate.io交易所API路由

提供Gate.io交易所的REST API接口
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field

from ..services.gateio_service import get_gateio_service, GateIOExchangeService
from ..core.security import get_current_user
from ..schemas.user import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gateio", tags=["Gate.io交易所"])


# ==================== 请求/响应模型 ====================

class MarketTickerResponse(BaseModel):
    """市场行情响应模型"""
    symbol: str = Field(..., description="交易对符号")
    price: float = Field(..., description="最新价格")
    bid_price: float = Field(..., description="买一价")
    ask_price: float = Field(..., description="卖一价")
    volume_24h: float = Field(..., description="24小时成交量")
    quote_volume_24h: float = Field(..., description="24小时成交额")
    price_change_24h: float = Field(..., description="24小时价格变化百分比")
    high_24h: float = Field(..., description="24小时最高价")
    low_24h: float = Field(..., description="24小时最低价")
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
    quote_volume: float = Field(..., description="成交额")


class AccountBalanceResponse(BaseModel):
    """账户余额响应模型"""
    market_type: str = Field(..., description="市场类型")
    balances: Optional[List[Dict[str, Any]]] = Field(None, description="余额列表")
    total_balance: Optional[float] = Field(None, description="总余额")
    available_balance: Optional[float] = Field(None, description="可用余额")
    position_margin: Optional[float] = Field(None, description="持仓保证金")
    order_margin: Optional[float] = Field(None, description="委托保证金")
    unrealized_pnl: Optional[float] = Field(None, description="未实现盈亏")
    currency: Optional[str] = Field(None, description="币种")
    timestamp: str = Field(..., description="时间戳")


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
    risk_limit: float = Field(..., description="风险限额")
    mode: str = Field(..., description="持仓模式")
    timestamp: str = Field(..., description="时间戳")


class CreateOrderRequest(BaseModel):
    """创建订单请求模型"""
    symbol: str = Field(..., description="交易对/合约符号")
    side: str = Field(..., description="买卖方向 (buy/sell)")
    order_type: str = Field(..., description="订单类型 (limit/market)")
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


# ==================== 市场数据接口 ====================

@router.get("/exchange-info", summary="获取交易所信息")
async def get_exchange_info(
    gateio_service: GateIOExchangeService = Depends(get_gateio_service)
) -> Dict[str, Any]:
    """
    获取Gate.io交易所基本信息
    
    Returns:
        交易所信息
    """
    try:
        return await gateio_service.get_exchange_info()
    except Exception as e:
        logger.error(f"获取交易所信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取交易所信息失败: {str(e)}")


@router.get("/ticker/{symbol}", response_model=MarketTickerResponse, summary="获取行情数据")
async def get_ticker(
    symbol: str,
    market_type: str = Query(default="spot", description="市场类型 (spot/futures)"),
    gateio_service: GateIOExchangeService = Depends(get_gateio_service)
) -> MarketTickerResponse:
    """
    获取指定交易对的行情数据
    
    Args:
        symbol: 交易对符号，如 BTC_USDT
        market_type: 市场类型 (spot/futures)
        
    Returns:
        行情数据
    """
    try:
        if market_type == "spot":
            ticker_data = await gateio_service.get_spot_ticker(symbol)
        else:
            ticker_data = await gateio_service.get_futures_ticker(symbol)
        
        if not ticker_data:
            raise HTTPException(status_code=404, detail=f"未找到交易对 {symbol} 的行情数据")
        
        return MarketTickerResponse(**ticker_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取行情数据失败 {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"获取行情数据失败: {str(e)}")


@router.get("/orderbook/{symbol}", response_model=OrderBookResponse, summary="获取订单簿")
async def get_order_book(
    symbol: str,
    market_type: str = Query(default="spot", description="市场类型 (spot/futures)"),
    limit: int = Query(default=20, ge=1, le=100, description="深度限制"),
    gateio_service: GateIOExchangeService = Depends(get_gateio_service)
) -> OrderBookResponse:
    """
    获取指定交易对的订单簿数据
    
    Args:
        symbol: 交易对符号
        market_type: 市场类型 (spot/futures)
        limit: 深度限制
        
    Returns:
        订单簿数据
    """
    try:
        order_book_data = await gateio_service.get_order_book(symbol, market_type, limit)
        return OrderBookResponse(**order_book_data)
        
    except Exception as e:
        logger.error(f"获取订单簿失败 {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"获取订单簿失败: {str(e)}")


@router.get("/trades/{symbol}", response_model=List[TradeResponse], summary="获取成交记录")
async def get_recent_trades(
    symbol: str,
    market_type: str = Query(default="spot", description="市场类型 (spot/futures)"),
    limit: int = Query(default=100, ge=1, le=500, description="记录数量限制"),
    gateio_service: GateIOExchangeService = Depends(get_gateio_service)
) -> List[TradeResponse]:
    """
    获取指定交易对的最近成交记录
    
    Args:
        symbol: 交易对符号
        market_type: 市场类型 (spot/futures)
        limit: 记录数量限制
        
    Returns:
        成交记录列表
    """
    try:
        trades_data = await gateio_service.get_recent_trades(symbol, market_type, limit)
        return [TradeResponse(**trade) for trade in trades_data]
        
    except Exception as e:
        logger.error(f"获取成交记录失败 {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"获取成交记录失败: {str(e)}")


@router.get("/klines/{symbol}", response_model=List[KlineResponse], summary="获取K线数据")
async def get_klines(
    symbol: str,
    interval: str = Query(default="1m", description="时间间隔"),
    market_type: str = Query(default="spot", description="市场类型 (spot/futures)"),
    limit: int = Query(default=100, ge=1, le=1000, description="数量限制"),
    start_time: Optional[int] = Query(None, description="开始时间戳"),
    end_time: Optional[int] = Query(None, description="结束时间戳"),
    gateio_service: GateIOExchangeService = Depends(get_gateio_service)
) -> List[KlineResponse]:
    """
    获取指定交易对的K线数据
    
    Args:
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
        klines_data = await gateio_service.get_klines(
            symbol, interval, market_type, limit, start_time, end_time
        )
        return [KlineResponse(**kline) for kline in klines_data]
        
    except Exception as e:
        logger.error(f"获取K线数据失败 {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"获取K线数据失败: {str(e)}")


# ==================== 账户管理接口 ====================

@router.get("/account/balance", response_model=AccountBalanceResponse, summary="获取账户余额")
async def get_account_balance(
    market_type: str = Query(default="spot", description="市场类型 (spot/futures)"),
    current_user: UserResponse = Depends(get_current_user),
    gateio_service: GateIOExchangeService = Depends(get_gateio_service)
) -> AccountBalanceResponse:
    """
    获取当前用户的账户余额
    
    Args:
        market_type: 市场类型 (spot/futures)
        
    Returns:
        账户余额信息
    """
    try:
        balance_data = await gateio_service.get_account_balance(market_type)
        return AccountBalanceResponse(**balance_data)
        
    except Exception as e:
        logger.error(f"获取账户余额失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取账户余额失败: {str(e)}")


@router.get("/account/positions", response_model=List[PositionResponse], summary="获取持仓信息")
async def get_positions(
    settle: str = Query(default="usdt", description="结算货币"),
    current_user: UserResponse = Depends(get_current_user),
    gateio_service: GateIOExchangeService = Depends(get_gateio_service)
) -> List[PositionResponse]:
    """
    获取当前用户的期货持仓信息
    
    Args:
        settle: 结算货币
        
    Returns:
        持仓信息列表
    """
    try:
        positions_data = await gateio_service.get_positions(settle)
        return [PositionResponse(**position) for position in positions_data]
        
    except Exception as e:
        logger.error(f"获取持仓信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取持仓信息失败: {str(e)}")


# ==================== 交易执行接口 ====================

@router.post("/orders", response_model=OrderResponse, summary="创建订单")
async def create_order(
    order_request: CreateOrderRequest,
    current_user: UserResponse = Depends(get_current_user),
    gateio_service: GateIOExchangeService = Depends(get_gateio_service)
) -> OrderResponse:
    """
    创建新订单
    
    Args:
        order_request: 订单创建请求
        
    Returns:
        订单信息
    """
    try:
        order_data = await gateio_service.create_order(
            symbol=order_request.symbol,
            side=order_request.side,
            order_type=order_request.order_type,
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
        logger.error(f"创建订单失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建订单失败: {str(e)}")


@router.delete("/orders/{order_id}", summary="取消订单")
async def cancel_order(
    order_id: str,
    symbol: str = Query(..., description="交易对符号"),
    market_type: str = Query(default="spot", description="市场类型 (spot/futures)"),
    current_user: UserResponse = Depends(get_current_user),
    gateio_service: GateIOExchangeService = Depends(get_gateio_service)
) -> Dict[str, Any]:
    """
    取消指定订单
    
    Args:
        order_id: 订单ID
        symbol: 交易对符号
        market_type: 市场类型 (spot/futures)
        
    Returns:
        取消结果
    """
    try:
        result = await gateio_service.cancel_order(order_id, symbol, market_type)
        return result
        
    except Exception as e:
        logger.error(f"取消订单失败 {order_id}: {e}")
        raise HTTPException(status_code=500, detail=f"取消订单失败: {str(e)}")


@router.get("/orders/{order_id}", response_model=OrderResponse, summary="获取订单详情")
async def get_order(
    order_id: str,
    symbol: str = Query(..., description="交易对符号"),
    market_type: str = Query(default="spot", description="市场类型 (spot/futures)"),
    current_user: UserResponse = Depends(get_current_user),
    gateio_service: GateIOExchangeService = Depends(get_gateio_service)
) -> OrderResponse:
    """
    获取指定订单的详细信息
    
    Args:
        order_id: 订单ID
        symbol: 交易对符号
        market_type: 市场类型 (spot/futures)
        
    Returns:
        订单详情
    """
    try:
        order_data = await gateio_service.get_order(order_id, symbol, market_type)
        return OrderResponse(**order_data)
        
    except Exception as e:
        logger.error(f"获取订单详情失败 {order_id}: {e}")
        raise HTTPException(status_code=500, detail=f"获取订单详情失败: {str(e)}")


@router.get("/orders", response_model=List[OrderResponse], summary="获取订单列表")
async def get_orders(
    symbol: str = Query(..., description="交易对符号"),
    status: str = Query(default="open", description="订单状态"),
    market_type: str = Query(default="spot", description="市场类型 (spot/futures)"),
    limit: int = Query(default=100, ge=1, le=500, description="数量限制"),
    current_user: UserResponse = Depends(get_current_user),
    gateio_service: GateIOExchangeService = Depends(get_gateio_service)
) -> List[OrderResponse]:
    """
    获取订单列表
    
    Args:
        symbol: 交易对符号
        status: 订单状态
        market_type: 市场类型 (spot/futures)
        limit: 数量限制
        
    Returns:
        订单列表
    """
    try:
        orders_data = await gateio_service.get_orders(symbol, status, market_type, limit)
        return [OrderResponse(**order) for order in orders_data]
        
    except Exception as e:
        logger.error(f"获取订单列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取订单列表失败: {str(e)}")


# ==================== WebSocket数据流接口 ====================

@router.post("/websocket/ticker/start", summary="启动行情数据流")
async def start_ticker_stream(
    symbols: List[str] = Body(..., description="交易对符号列表"),
    market_type: str = Body(default="spot", description="市场类型 (spot/futures)"),
    current_user: UserResponse = Depends(get_current_user),
    gateio_service: GateIOExchangeService = Depends(get_gateio_service)
) -> Dict[str, Any]:
    """
    启动指定交易对的行情数据流
    
    Args:
        symbols: 交易对符号列表
        market_type: 市场类型 (spot/futures)
        
    Returns:
        启动结果
    """
    try:
        await gateio_service.start_ticker_stream(symbols, market_type)
        
        return {
            "status": "success",
            "message": f"已启动{market_type}行情数据流",
            "symbols": symbols,
            "market_type": market_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"启动行情数据流失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动行情数据流失败: {str(e)}")


@router.post("/websocket/trades/start", summary="启动成交数据流")
async def start_trades_stream(
    symbols: List[str] = Body(..., description="交易对符号列表"),
    market_type: str = Body(default="spot", description="市场类型 (spot/futures)"),
    current_user: UserResponse = Depends(get_current_user),
    gateio_service: GateIOExchangeService = Depends(get_gateio_service)
) -> Dict[str, Any]:
    """
    启动指定交易对的成交数据流
    
    Args:
        symbols: 交易对符号列表
        market_type: 市场类型 (spot/futures)
        
    Returns:
        启动结果
    """
    try:
        await gateio_service.start_trades_stream(symbols, market_type)
        
        return {
            "status": "success",
            "message": f"已启动{market_type}成交数据流",
            "symbols": symbols,
            "market_type": market_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"启动成交数据流失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动成交数据流失败: {str(e)}")


@router.post("/websocket/orderbook/start", summary="启动订单簿数据流")
async def start_order_book_stream(
    symbols: List[str] = Body(..., description="交易对符号列表"),
    market_type: str = Body(default="spot", description="市场类型 (spot/futures)"),
    interval: str = Body(default="100ms", description="更新间隔"),
    limit: int = Body(default=20, description="深度限制"),
    current_user: UserResponse = Depends(get_current_user),
    gateio_service: GateIOExchangeService = Depends(get_gateio_service)
) -> Dict[str, Any]:
    """
    启动指定交易对的订单簿数据流
    
    Args:
        symbols: 交易对符号列表
        market_type: 市场类型 (spot/futures)
        interval: 更新间隔
        limit: 深度限制
        
    Returns:
        启动结果
    """
    try:
        await gateio_service.start_order_book_stream(symbols, market_type, interval, limit)
        
        return {
            "status": "success",
            "message": f"已启动{market_type}订单簿数据流",
            "symbols": symbols,
            "market_type": market_type,
            "interval": interval,
            "limit": limit,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"启动订单簿数据流失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动订单簿数据流失败: {str(e)}")


@router.post("/websocket/orders/start", summary="启动订单更新数据流")
async def start_orders_stream(
    symbols: List[str] = Body(..., description="交易对符号列表"),
    market_type: str = Body(default="spot", description="市场类型 (spot/futures)"),
    current_user: UserResponse = Depends(get_current_user),
    gateio_service: GateIOExchangeService = Depends(get_gateio_service)
) -> Dict[str, Any]:
    """
    启动指定交易对的订单更新数据流（需要认证）
    
    Args:
        symbols: 交易对符号列表
        market_type: 市场类型 (spot/futures)
        
    Returns:
        启动结果
    """
    try:
        await gateio_service.start_orders_stream(symbols, market_type)
        
        return {
            "status": "success",
            "message": f"已启动{market_type}订单更新数据流",
            "symbols": symbols,
            "market_type": market_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"启动订单更新数据流失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动订单更新数据流失败: {str(e)}")