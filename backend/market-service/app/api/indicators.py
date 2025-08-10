#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 技术指标API路由

提供技术指标计算相关的API接口
"""

import logging
from typing import List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..services.market_service import get_market_service, MarketDataService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/indicators", tags=["技术指标"])


# ==================== 请求模型 ====================

class SMARequest(BaseModel):
    """简单移动平均线请求模型"""
    symbol: str = Field(..., description="交易对符号")
    interval: str = Field("1m", description="K线间隔")
    period: int = Field(20, description="计算周期", ge=1, le=200)
    market_type: str = Field("spot", description="市场类型 (spot/futures)")
    limit: int = Field(100, description="K线数量", ge=1, le=1000)


class EMARequest(BaseModel):
    """指数移动平均线请求模型"""
    symbol: str = Field(..., description="交易对符号")
    interval: str = Field("1m", description="K线间隔")
    period: int = Field(20, description="计算周期", ge=1, le=200)
    market_type: str = Field("spot", description="市场类型 (spot/futures)")
    limit: int = Field(100, description="K线数量", ge=1, le=1000)


class RSIRequest(BaseModel):
    """相对强弱指数请求模型"""
    symbol: str = Field(..., description="交易对符号")
    interval: str = Field("1m", description="K线间隔")
    period: int = Field(14, description="计算周期", ge=1, le=100)
    market_type: str = Field("spot", description="市场类型 (spot/futures)")
    limit: int = Field(100, description="K线数量", ge=1, le=1000)


class MACDRequest(BaseModel):
    """MACD请求模型"""
    symbol: str = Field(..., description="交易对符号")
    interval: str = Field("1m", description="K线间隔")
    fast_period: int = Field(12, description="快线周期", ge=1, le=100)
    slow_period: int = Field(26, description="慢线周期", ge=1, le=100)
    signal_period: int = Field(9, description="信号线周期", ge=1, le=100)
    market_type: str = Field("spot", description="市场类型 (spot/futures)")
    limit: int = Field(100, description="K线数量", ge=1, le=1000)


class BollingerBandsRequest(BaseModel):
    """布林带请求模型"""
    symbol: str = Field(..., description="交易对符号")
    interval: str = Field("1m", description="K线间隔")
    period: int = Field(20, description="计算周期", ge=1, le=100)
    std_dev: float = Field(2.0, description="标准差倍数", ge=0.1, le=5.0)
    market_type: str = Field("spot", description="市场类型 (spot/futures)")
    limit: int = Field(100, description="K线数量", ge=1, le=1000)


# ==================== 响应模型 ====================

class ApiResponse(BaseModel):
    """API响应基础模型"""
    success: bool = Field(..., description="请求是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")


class IndicatorData(BaseModel):
    """技术指标数据模型"""
    symbol: str = Field(..., description="交易对符号")
    interval: str = Field(..., description="K线间隔")
    values: List[float] = Field(..., description="指标值列表")
    timestamps: List[int] = Field(..., description="时间戳列表")


class MACDData(BaseModel):
    """MACD数据模型"""
    symbol: str = Field(..., description="交易对符号")
    interval: str = Field(..., description="K线间隔")
    macd_line: List[float] = Field(..., description="MACD线")
    signal_line: List[float] = Field(..., description="信号线")
    histogram: List[float] = Field(..., description="柱状图")
    timestamps: List[int] = Field(..., description="时间戳列表")


class BollingerBandsData(BaseModel):
    """布林带数据模型"""
    symbol: str = Field(..., description="交易对符号")
    interval: str = Field(..., description="K线间隔")
    upper_band: List[float] = Field(..., description="上轨")
    middle_band: List[float] = Field(..., description="中轨")
    lower_band: List[float] = Field(..., description="下轨")
    timestamps: List[int] = Field(..., description="时间戳列表")


# ==================== 辅助函数 ====================

async def get_kline_data(market_service: MarketDataService, symbol: str, interval: str, market_type: str, limit: int):
    """获取K线数据"""
    klines = await market_service.get_candlesticks(
        symbol=symbol,
        interval=interval,
        market_type=market_type,
        limit=limit
    )
    
    if not klines:
        raise HTTPException(status_code=404, detail="未找到K线数据")
    
    # 提取收盘价和时间戳
    close_prices = [float(kline[2]) for kline in klines]  # 收盘价在索引2
    timestamps = [int(kline[0]) for kline in klines]  # 时间戳在索引0
    
    return close_prices, timestamps


def calculate_macd(prices: List[float], fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
    """计算MACD指标"""
    if len(prices) < slow_period:
        return [], [], []
    
    # 计算EMA
    def ema(data, period):
        multiplier = 2 / (period + 1)
        ema_values = [sum(data[:period]) / period]
        for i in range(period, len(data)):
            ema_val = (data[i] * multiplier) + (ema_values[-1] * (1 - multiplier))
            ema_values.append(ema_val)
        return ema_values
    
    # 计算快线和慢线EMA
    fast_ema = ema(prices, fast_period)
    slow_ema = ema(prices, slow_period)
    
    # 计算MACD线
    macd_line = []
    start_index = slow_period - fast_period
    for i in range(len(slow_ema)):
        macd_val = fast_ema[i + start_index] - slow_ema[i]
        macd_line.append(macd_val)
    
    # 计算信号线
    signal_line = ema(macd_line, signal_period)
    
    # 计算柱状图
    histogram = []
    signal_start = signal_period - 1
    for i in range(len(signal_line)):
        hist_val = macd_line[i + signal_start] - signal_line[i]
        histogram.append(hist_val)
    
    return macd_line, signal_line, histogram


def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0):
    """计算布林带"""
    if len(prices) < period:
        return [], [], []
    
    upper_band = []
    middle_band = []
    lower_band = []
    
    for i in range(period - 1, len(prices)):
        # 计算移动平均
        sma = sum(prices[i - period + 1:i + 1]) / period
        
        # 计算标准差
        variance = sum([(price - sma) ** 2 for price in prices[i - period + 1:i + 1]]) / period
        std = variance ** 0.5
        
        # 计算布林带
        upper = sma + (std_dev * std)
        lower = sma - (std_dev * std)
        
        upper_band.append(upper)
        middle_band.append(sma)
        lower_band.append(lower)
    
    return upper_band, middle_band, lower_band


# ==================== API路由 ====================

@router.get("/sma", response_model=ApiResponse)
async def get_sma(
    symbol: str = Query(..., description="交易对符号"),
    interval: str = Query("1m", description="K线间隔"),
    period: int = Query(20, description="计算周期", ge=1, le=200),
    market_type: str = Query("spot", description="市场类型 (spot/futures)"),
    limit: int = Query(100, description="K线数量", ge=1, le=1000),
    market_service: MarketDataService = Depends(get_market_service)
):
    """
    计算简单移动平均线 (SMA)
    """
    try:
        # 获取K线数据
        close_prices, timestamps = await get_kline_data(
            market_service, symbol, interval, market_type, limit
        )
        
        # 计算SMA
        sma_values = market_service.calculate_sma(close_prices, period)
        
        if not sma_values:
            raise HTTPException(status_code=400, detail="数据不足，无法计算SMA")
        
        # 对应的时间戳
        sma_timestamps = timestamps[period - 1:]
        
        result = {
            "symbol": symbol,
            "interval": interval,
            "period": period,
            "values": sma_values,
            "timestamps": sma_timestamps
        }
        
        return ApiResponse(
            success=True,
            message="SMA计算成功",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SMA计算失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.get("/ema", response_model=ApiResponse)
async def get_ema(
    symbol: str = Query(..., description="交易对符号"),
    interval: str = Query("1m", description="K线间隔"),
    period: int = Query(20, description="计算周期", ge=1, le=200),
    market_type: str = Query("spot", description="市场类型 (spot/futures)"),
    limit: int = Query(100, description="K线数量", ge=1, le=1000),
    market_service: MarketDataService = Depends(get_market_service)
):
    """
    计算指数移动平均线 (EMA)
    """
    try:
        # 获取K线数据
        close_prices, timestamps = await get_kline_data(
            market_service, symbol, interval, market_type, limit
        )
        
        # 计算EMA
        ema_values = market_service.calculate_ema(close_prices, period)
        
        if not ema_values:
            raise HTTPException(status_code=400, detail="数据不足，无法计算EMA")
        
        # 对应的时间戳
        ema_timestamps = timestamps[period:]
        
        result = {
            "symbol": symbol,
            "interval": interval,
            "period": period,
            "values": ema_values,
            "timestamps": ema_timestamps
        }
        
        return ApiResponse(
            success=True,
            message="EMA计算成功",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"EMA计算失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.get("/rsi", response_model=ApiResponse)
async def get_rsi(
    symbol: str = Query(..., description="交易对符号"),
    interval: str = Query("1m", description="K线间隔"),
    period: int = Query(14, description="计算周期", ge=1, le=100),
    market_type: str = Query("spot", description="市场类型 (spot/futures)"),
    limit: int = Query(100, description="K线数量", ge=1, le=1000),
    market_service: MarketDataService = Depends(get_market_service)
):
    """
    计算相对强弱指数 (RSI)
    """
    try:
        # 获取K线数据
        close_prices, timestamps = await get_kline_data(
            market_service, symbol, interval, market_type, limit
        )
        
        # 计算RSI
        rsi_values = market_service.calculate_rsi(close_prices, period)
        
        if not rsi_values:
            raise HTTPException(status_code=400, detail="数据不足，无法计算RSI")
        
        # 对应的时间戳
        rsi_timestamps = timestamps[period + 1:]
        
        result = {
            "symbol": symbol,
            "interval": interval,
            "period": period,
            "values": rsi_values,
            "timestamps": rsi_timestamps
        }
        
        return ApiResponse(
            success=True,
            message="RSI计算成功",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RSI计算失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.get("/macd", response_model=ApiResponse)
async def get_macd(
    symbol: str = Query(..., description="交易对符号"),
    interval: str = Query("1m", description="K线间隔"),
    fast_period: int = Query(12, description="快线周期", ge=1, le=100),
    slow_period: int = Query(26, description="慢线周期", ge=1, le=100),
    signal_period: int = Query(9, description="信号线周期", ge=1, le=100),
    market_type: str = Query("spot", description="市场类型 (spot/futures)"),
    limit: int = Query(100, description="K线数量", ge=1, le=1000),
    market_service: MarketDataService = Depends(get_market_service)
):
    """
    计算MACD指标
    """
    try:
        if fast_period >= slow_period:
            raise HTTPException(status_code=400, detail="快线周期必须小于慢线周期")
        
        # 获取K线数据
        close_prices, timestamps = await get_kline_data(
            market_service, symbol, interval, market_type, limit
        )
        
        # 计算MACD
        macd_line, signal_line, histogram = calculate_macd(
            close_prices, fast_period, slow_period, signal_period
        )
        
        if not macd_line:
            raise HTTPException(status_code=400, detail="数据不足，无法计算MACD")
        
        # 对应的时间戳
        macd_timestamps = timestamps[slow_period + signal_period - 1:]
        
        result = {
            "symbol": symbol,
            "interval": interval,
            "fast_period": fast_period,
            "slow_period": slow_period,
            "signal_period": signal_period,
            "macd_line": macd_line[signal_period - 1:],
            "signal_line": signal_line,
            "histogram": histogram,
            "timestamps": macd_timestamps
        }
        
        return ApiResponse(
            success=True,
            message="MACD计算成功",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MACD计算失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.get("/bollinger-bands", response_model=ApiResponse)
async def get_bollinger_bands(
    symbol: str = Query(..., description="交易对符号"),
    interval: str = Query("1m", description="K线间隔"),
    period: int = Query(20, description="计算周期", ge=1, le=100),
    std_dev: float = Query(2.0, description="标准差倍数", ge=0.1, le=5.0),
    market_type: str = Query("spot", description="市场类型 (spot/futures)"),
    limit: int = Query(100, description="K线数量", ge=1, le=1000),
    market_service: MarketDataService = Depends(get_market_service)
):
    """
    计算布林带指标
    """
    try:
        # 获取K线数据
        close_prices, timestamps = await get_kline_data(
            market_service, symbol, interval, market_type, limit
        )
        
        # 计算布林带
        upper_band, middle_band, lower_band = calculate_bollinger_bands(
            close_prices, period, std_dev
        )
        
        if not upper_band:
            raise HTTPException(status_code=400, detail="数据不足，无法计算布林带")
        
        # 对应的时间戳
        bb_timestamps = timestamps[period - 1:]
        
        result = {
            "symbol": symbol,
            "interval": interval,
            "period": period,
            "std_dev": std_dev,
            "upper_band": upper_band,
            "middle_band": middle_band,
            "lower_band": lower_band,
            "timestamps": bb_timestamps
        }
        
        return ApiResponse(
            success=True,
            message="布林带计算成功",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"布林带计算失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


# ==================== POST方式的API ====================

@router.post("/sma", response_model=ApiResponse)
async def post_sma(
    request: SMARequest,
    market_service: MarketDataService = Depends(get_market_service)
):
    """
    计算简单移动平均线 (SMA) - POST方式
    """
    return await get_sma(
        symbol=request.symbol,
        interval=request.interval,
        period=request.period,
        market_type=request.market_type,
        limit=request.limit,
        market_service=market_service
    )


@router.post("/ema", response_model=ApiResponse)
async def post_ema(
    request: EMARequest,
    market_service: MarketDataService = Depends(get_market_service)
):
    """
    计算指数移动平均线 (EMA) - POST方式
    """
    return await get_ema(
        symbol=request.symbol,
        interval=request.interval,
        period=request.period,
        market_type=request.market_type,
        limit=request.limit,
        market_service=market_service
    )


@router.post("/rsi", response_model=ApiResponse)
async def post_rsi(
    request: RSIRequest,
    market_service: MarketDataService = Depends(get_market_service)
):
    """
    计算相对强弱指数 (RSI) - POST方式
    """
    return await get_rsi(
        symbol=request.symbol,
        interval=request.interval,
        period=request.period,
        market_type=request.market_type,
        limit=request.limit,
        market_service=market_service
    )


@router.post("/macd", response_model=ApiResponse)
async def post_macd(
    request: MACDRequest,
    market_service: MarketDataService = Depends(get_market_service)
):
    """
    计算MACD指标 - POST方式
    """
    return await get_macd(
        symbol=request.symbol,
        interval=request.interval,
        fast_period=request.fast_period,
        slow_period=request.slow_period,
        signal_period=request.signal_period,
        market_type=request.market_type,
        limit=request.limit,
        market_service=market_service
    )


@router.post("/bollinger-bands", response_model=ApiResponse)
async def post_bollinger_bands(
    request: BollingerBandsRequest,
    market_service: MarketDataService = Depends(get_market_service)
):
    """
    计算布林带指标 - POST方式
    """
    return await get_bollinger_bands(
        symbol=request.symbol,
        interval=request.interval,
        period=request.period,
        std_dev=request.std_dev,
        market_type=request.market_type,
        limit=request.limit,
        market_service=market_service
    )