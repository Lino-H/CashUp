from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from shared.exchanges import ExchangeType, Symbol, Ticker, OrderBook, Trade, Kline
from ..core.exchange_pool import exchange_pool

router = APIRouter()


class SymbolResponse(BaseModel):
    """交易对响应"""
    symbol: str
    base_asset: str
    quote_asset: str
    status: str
    min_qty: float
    max_qty: float
    step_size: float
    min_price: float
    max_price: float
    tick_size: float
    min_notional: float


class TickerResponse(BaseModel):
    """行情响应"""
    symbol: str
    last_price: float
    bid_price: float
    ask_price: float
    bid_qty: float
    ask_qty: float
    volume_24h: float
    change_24h: float
    high_24h: float
    low_24h: float
    timestamp: int


class OrderBookResponse(BaseModel):
    """订单簿响应"""
    symbol: str
    bids: List[List[float]]
    asks: List[List[float]]
    timestamp: int


class TradeResponse(BaseModel):
    """成交记录响应"""
    id: str
    symbol: str
    price: float
    qty: float
    side: str
    timestamp: int


class KlineResponse(BaseModel):
    """K线响应"""
    symbol: str
    open_time: int
    close_time: int
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    quote_volume: float
    trades_count: int


def _convert_symbol_to_response(symbol: Symbol) -> SymbolResponse:
    """转换Symbol对象为响应格式"""
    return SymbolResponse(
        symbol=symbol.symbol,
        base_asset=symbol.base_asset,
        quote_asset=symbol.quote_asset,
        status=symbol.status,
        min_qty=symbol.min_qty,
        max_qty=symbol.max_qty,
        step_size=symbol.step_size,
        min_price=symbol.min_price,
        max_price=symbol.max_price,
        tick_size=symbol.tick_size,
        min_notional=symbol.min_notional
    )


def _convert_ticker_to_response(ticker: Ticker) -> TickerResponse:
    """转换Ticker对象为响应格式"""
    return TickerResponse(
        symbol=ticker.symbol,
        last_price=ticker.last_price,
        bid_price=ticker.bid_price,
        ask_price=ticker.ask_price,
        bid_qty=ticker.bid_qty,
        ask_qty=ticker.ask_qty,
        volume_24h=ticker.volume_24h,
        change_24h=ticker.change_24h,
        high_24h=ticker.high_24h,
        low_24h=ticker.low_24h,
        timestamp=ticker.timestamp
    )


def _convert_order_book_to_response(order_book: OrderBook) -> OrderBookResponse:
    """转换OrderBook对象为响应格式"""
    return OrderBookResponse(
        symbol=order_book.symbol,
        bids=order_book.bids,
        asks=order_book.asks,
        timestamp=order_book.timestamp
    )


def _convert_trade_to_response(trade: Trade) -> TradeResponse:
    """转换Trade对象为响应格式"""
    return TradeResponse(
        id=trade.id,
        symbol=trade.symbol,
        price=trade.price,
        qty=trade.qty,
        side=trade.side.value,
        timestamp=trade.timestamp
    )


def _convert_kline_to_response(kline: Kline) -> KlineResponse:
    """转换Kline对象为响应格式"""
    return KlineResponse(
        symbol=kline.symbol,
        open_time=kline.open_time,
        close_time=kline.close_time,
        open_price=kline.open_price,
        high_price=kline.high_price,
        low_price=kline.low_price,
        close_price=kline.close_price,
        volume=kline.volume,
        quote_volume=kline.quote_volume,
        trades_count=kline.trades_count
    )


@router.get("/symbols/{exchange_name}", response_model=List[SymbolResponse])
async def get_symbols(
    exchange_name: str,
    exchange_type: str = Query("spot", description="交易类型: spot, futures")
):
    """获取交易对列表"""
    try:
        # 验证交易类型
        try:
            ex_type = ExchangeType(exchange_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的交易类型: {exchange_type}")
        
        # 获取默认交易所实例
        async with exchange_pool.get_default_exchange_context(exchange_name) as exchange:
            symbols = await exchange.get_symbols(ex_type)
            return [_convert_symbol_to_response(symbol) for symbol in symbols]
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易对列表失败: {str(e)}")


@router.get("/ticker/{exchange_name}/{symbol}", response_model=TickerResponse)
async def get_ticker(
    exchange_name: str,
    symbol: str,
    exchange_type: str = Query("spot", description="交易类型: spot, futures")
):
    """获取单个交易对行情"""
    try:
        # 验证交易类型
        try:
            ex_type = ExchangeType(exchange_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的交易类型: {exchange_type}")
        
        # 获取默认交易所实例
        async with exchange_pool.get_default_exchange_context(exchange_name) as exchange:
            ticker = await exchange.get_ticker(symbol, ex_type)
            return _convert_ticker_to_response(ticker)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取行情失败: {str(e)}")


@router.get("/tickers/{exchange_name}", response_model=List[TickerResponse])
async def get_tickers(
    exchange_name: str,
    exchange_type: str = Query("spot", description="交易类型: spot, futures")
):
    """获取所有交易对行情"""
    try:
        # 验证交易类型
        try:
            ex_type = ExchangeType(exchange_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的交易类型: {exchange_type}")
        
        # 获取默认交易所实例
        async with exchange_pool.get_default_exchange_context(exchange_name) as exchange:
            tickers = await exchange.get_tickers(ex_type)
            return [_convert_ticker_to_response(ticker) for ticker in tickers]
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取行情列表失败: {str(e)}")


@router.get("/orderbook/{exchange_name}/{symbol}", response_model=OrderBookResponse)
async def get_order_book(
    exchange_name: str,
    symbol: str,
    limit: int = Query(100, ge=1, le=1000, description="订单簿深度"),
    exchange_type: str = Query("spot", description="交易类型: spot, futures")
):
    """获取订单簿"""
    try:
        # 验证交易类型
        try:
            ex_type = ExchangeType(exchange_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的交易类型: {exchange_type}")
        
        # 获取默认交易所实例
        async with exchange_pool.get_default_exchange_context(exchange_name) as exchange:
            order_book = await exchange.get_order_book(symbol, limit, ex_type)
            return _convert_order_book_to_response(order_book)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取订单簿失败: {str(e)}")


@router.get("/trades/{exchange_name}/{symbol}", response_model=List[TradeResponse])
async def get_trades(
    exchange_name: str,
    symbol: str,
    limit: int = Query(100, ge=1, le=1000, description="成交记录数量"),
    exchange_type: str = Query("spot", description="交易类型: spot, futures")
):
    """获取成交记录"""
    try:
        # 验证交易类型
        try:
            ex_type = ExchangeType(exchange_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的交易类型: {exchange_type}")
        
        # 获取默认交易所实例
        async with exchange_pool.get_default_exchange_context(exchange_name) as exchange:
            trades = await exchange.get_trades(symbol, limit, ex_type)
            return [_convert_trade_to_response(trade) for trade in trades]
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取成交记录失败: {str(e)}")


@router.get("/klines/{exchange_name}/{symbol}", response_model=List[KlineResponse])
async def get_klines(
    exchange_name: str,
    symbol: str,
    interval: str = Query("1m", description="K线间隔: 1m, 5m, 15m, 30m, 1h, 4h, 1d等"),
    limit: int = Query(100, ge=1, le=1000, description="K线数量"),
    start_time: Optional[int] = Query(None, description="开始时间戳（毫秒）"),
    end_time: Optional[int] = Query(None, description="结束时间戳（毫秒）"),
    exchange_type: str = Query("spot", description="交易类型: spot, futures")
):
    """获取K线数据"""
    try:
        # 验证交易类型
        try:
            ex_type = ExchangeType(exchange_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的交易类型: {exchange_type}")
        
        # 获取默认交易所实例
        async with exchange_pool.get_default_exchange_context(exchange_name) as exchange:
            klines = await exchange.get_klines(
                symbol, interval, limit, start_time, end_time, ex_type
            )
            return [_convert_kline_to_response(kline) for kline in klines]
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取K线数据失败: {str(e)}")