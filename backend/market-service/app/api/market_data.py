#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 市场数据API路由

提供市场数据相关的API接口
"""

import logging
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..services.market_service import get_market_service, MarketDataService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market-data", tags=["市场数据"])


# ==================== 请求模型 ====================

class TickerRequest(BaseModel):
    """行情请求模型"""
    symbol: str = Field(..., description="交易对符号")
    market_type: str = Field("spot", description="市场类型 (spot/futures)")


class OrderBookRequest(BaseModel):
    """订单簿请求模型"""
    symbol: str = Field(..., description="交易对符号")
    market_type: str = Field("spot", description="市场类型 (spot/futures)")
    limit: int = Field(20, description="深度限制", ge=1, le=100)


class TradesRequest(BaseModel):
    """成交记录请求模型"""
    symbol: str = Field(..., description="交易对符号")
    market_type: str = Field("spot", description="市场类型 (spot/futures)")
    limit: int = Field(100, description="记录数量限制", ge=1, le=1000)


class CandlesticksRequest(BaseModel):
    """K线请求模型"""
    symbol: str = Field(..., description="交易对符号")
    interval: str = Field("1m", description="K线间隔")
    market_type: str = Field("spot", description="市场类型 (spot/futures)")
    limit: int = Field(100, description="数量限制", ge=1, le=1000)
    from_time: Optional[int] = Field(None, description="开始时间戳")
    to_time: Optional[int] = Field(None, description="结束时间戳")


# ==================== 响应模型 ====================

class ApiResponse(BaseModel):
    """API响应基础模型"""
    success: bool = Field(..., description="请求是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")


class SupportedPairsResponse(BaseModel):
    """支持的交易对响应模型"""
    spot: List[str] = Field(..., description="现货交易对列表")
    futures: List[str] = Field(..., description="期货合约列表")


class TickerData(BaseModel):
    """行情数据模型"""
    symbol: str = Field(..., description="交易对符号")
    last: str = Field(..., description="最新价格")
    change_percentage: str = Field(..., description="24小时涨跌幅")
    high_24h: str = Field(..., description="24小时最高价")
    low_24h: str = Field(..., description="24小时最低价")
    volume_24h: str = Field(..., description="24小时成交量")
    quote_volume_24h: str = Field(..., description="24小时成交额")


class OrderBookData(BaseModel):
    """订单簿数据模型"""
    asks: List[List[str]] = Field(..., description="卖单列表 [价格, 数量]")
    bids: List[List[str]] = Field(..., description="买单列表 [价格, 数量]")
    current: int = Field(..., description="当前时间戳")
    update: int = Field(..., description="更新时间戳")


class TradeData(BaseModel):
    """成交数据模型"""
    id: str = Field(..., description="成交ID")
    create_time: str = Field(..., description="成交时间")
    side: str = Field(..., description="成交方向 (buy/sell)")
    amount: str = Field(..., description="成交数量")
    price: str = Field(..., description="成交价格")


# ==================== API路由 ====================

@router.get("/supported-pairs", response_model=ApiResponse)
async def get_supported_pairs(
    market_type: str = Query("all", description="市场类型 (spot/futures/all)"),
    market_service: MarketDataService = Depends(get_market_service)
):
    """
    获取支持的交易对列表
    """
    try:
        data = await market_service.get_supported_pairs(market_type)
        
        return ApiResponse(
            success=True,
            message="获取支持的交易对成功",
            data=data
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取支持的交易对失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.get("/ticker", response_model=ApiResponse)
async def get_ticker(
    symbol: str = Query(..., description="交易对符号"),
    market_type: str = Query("spot", description="市场类型 (spot/futures)"),
    market_service: MarketDataService = Depends(get_market_service)
):
    """
    获取行情数据
    """
    try:
        data = await market_service.get_ticker(symbol, market_type)
        
        if data is None:
            raise HTTPException(status_code=404, detail="未找到行情数据")
        
        return ApiResponse(
            success=True,
            message="获取行情数据成功",
            data=data
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取行情数据失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.get("/order-book", response_model=ApiResponse)
async def get_order_book(
    symbol: str = Query(..., description="交易对符号"),
    market_type: str = Query("spot", description="市场类型 (spot/futures)"),
    limit: int = Query(20, description="深度限制", ge=1, le=100),
    market_service: MarketDataService = Depends(get_market_service)
):
    """
    获取订单簿数据
    """
    try:
        data = await market_service.get_order_book(symbol, market_type, limit)
        
        if data is None:
            raise HTTPException(status_code=404, detail="未找到订单簿数据")
        
        return ApiResponse(
            success=True,
            message="获取订单簿数据成功",
            data=data
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取订单簿数据失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.get("/trades", response_model=ApiResponse)
async def get_trades(
    symbol: str = Query(..., description="交易对符号"),
    market_type: str = Query("spot", description="市场类型 (spot/futures)"),
    limit: int = Query(100, description="记录数量限制", ge=1, le=1000),
    market_service: MarketDataService = Depends(get_market_service)
):
    """
    获取成交记录
    """
    try:
        data = await market_service.get_trades(symbol, market_type, limit)
        
        if data is None:
            raise HTTPException(status_code=404, detail="未找到成交记录")
        
        return ApiResponse(
            success=True,
            message="获取成交记录成功",
            data=data
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取成交记录失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.get("/candlesticks", response_model=ApiResponse)
async def get_candlesticks(
    symbol: str = Query(..., description="交易对符号"),
    interval: str = Query("1m", description="K线间隔"),
    market_type: str = Query("spot", description="市场类型 (spot/futures)"),
    limit: int = Query(100, description="数量限制", ge=1, le=1000),
    from_time: Optional[int] = Query(None, description="开始时间戳"),
    to_time: Optional[int] = Query(None, description="结束时间戳"),
    market_service: MarketDataService = Depends(get_market_service)
):
    """
    获取K线数据
    """
    try:
        data = await market_service.get_candlesticks(
            symbol=symbol,
            interval=interval,
            market_type=market_type,
            limit=limit,
            from_time=from_time,
            to_time=to_time
        )
        
        if data is None:
            raise HTTPException(status_code=404, detail="未找到K线数据")
        
        return ApiResponse(
            success=True,
            message="获取K线数据成功",
            data=data
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取K线数据失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.post("/ticker", response_model=ApiResponse)
async def post_ticker(
    request: TickerRequest,
    market_service: MarketDataService = Depends(get_market_service)
):
    """
    获取行情数据 (POST方式)
    """
    try:
        data = await market_service.get_ticker(request.symbol, request.market_type)
        
        if data is None:
            raise HTTPException(status_code=404, detail="未找到行情数据")
        
        return ApiResponse(
            success=True,
            message="获取行情数据成功",
            data=data
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取行情数据失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.post("/order-book", response_model=ApiResponse)
async def post_order_book(
    request: OrderBookRequest,
    market_service: MarketDataService = Depends(get_market_service)
):
    """
    获取订单簿数据 (POST方式)
    """
    try:
        data = await market_service.get_order_book(
            request.symbol,
            request.market_type,
            request.limit
        )
        
        if data is None:
            raise HTTPException(status_code=404, detail="未找到订单簿数据")
        
        return ApiResponse(
            success=True,
            message="获取订单簿数据成功",
            data=data
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取订单簿数据失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.post("/trades", response_model=ApiResponse)
async def post_trades(
    request: TradesRequest,
    market_service: MarketDataService = Depends(get_market_service)
):
    """
    获取成交记录 (POST方式)
    """
    try:
        data = await market_service.get_trades(
            request.symbol,
            request.market_type,
            request.limit
        )
        
        if data is None:
            raise HTTPException(status_code=404, detail="未找到成交记录")
        
        return ApiResponse(
            success=True,
            message="获取成交记录成功",
            data=data
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取成交记录失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.post("/candlesticks", response_model=ApiResponse)
async def post_candlesticks(
    request: CandlesticksRequest,
    market_service: MarketDataService = Depends(get_market_service)
):
    """
    获取K线数据 (POST方式)
    """
    try:
        data = await market_service.get_candlesticks(
            symbol=request.symbol,
            interval=request.interval,
            market_type=request.market_type,
            limit=request.limit,
            from_time=request.from_time,
            to_time=request.to_time
        )
        
        if data is None:
            raise HTTPException(status_code=404, detail="未找到K线数据")
        
        return ApiResponse(
            success=True,
            message="获取K线数据成功",
            data=data
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取K线数据失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


# ==================== WebSocket相关 ====================

@router.get("/ws/status", response_model=ApiResponse)
async def get_websocket_status(
    market_service: MarketDataService = Depends(get_market_service)
):
    """
    获取WebSocket连接状态
    """
    try:
        status = {
            "spot_running": market_service.gateio_client.ws.spot_running if market_service.gateio_client else False,
            "futures_running": market_service.gateio_client.ws.futures_running if market_service.gateio_client else False,
            "spot_connected": market_service.gateio_client.ws.spot_ws is not None if market_service.gateio_client else False,
            "futures_connected": market_service.gateio_client.ws.futures_ws is not None if market_service.gateio_client else False
        }
        
        return ApiResponse(
            success=True,
            message="获取WebSocket状态成功",
            data=status
        )
        
    except Exception as e:
        logger.error(f"获取WebSocket状态失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.post("/ws/restart", response_model=ApiResponse)
async def restart_websocket(
    market_type: str = Query("all", description="重启类型 (spot/futures/all)"),
    market_service: MarketDataService = Depends(get_market_service)
):
    """
    重启WebSocket连接
    """
    try:
        if not market_service.gateio_client:
            raise HTTPException(status_code=503, detail="市场数据服务未初始化")
        
        if market_type in ["spot", "all"]:
            await market_service.gateio_client.ws.stop_spot()
            await market_service.gateio_client.ws.start_spot()
        
        if market_type in ["futures", "all"]:
            await market_service.gateio_client.ws.stop_futures()
            await market_service.gateio_client.ws.start_futures()
        
        return ApiResponse(
            success=True,
            message=f"WebSocket {market_type} 连接重启成功",
            data=None
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重启WebSocket连接失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")