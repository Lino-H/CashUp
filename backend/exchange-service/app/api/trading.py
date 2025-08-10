from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from shared.exchanges import ExchangeType, OrderType, OrderSide, OrderStatus, Balance, Order, Position
from ..core.exchange_pool import exchange_pool

router = APIRouter()


class BalanceResponse(BaseModel):
    """余额响应"""
    asset: str
    free: float
    locked: float
    total: float


class OrderRequest(BaseModel):
    """订单请求"""
    symbol: str
    side: str  # buy, sell
    type: str  # market, limit, stop, stop_limit
    qty: float
    price: Optional[float] = None
    client_order_id: Optional[str] = None
    exchange_type: str = "spot"


class OrderResponse(BaseModel):
    """订单响应"""
    id: str
    client_order_id: str
    symbol: str
    side: str
    type: str
    qty: float
    price: Optional[float]
    status: str
    filled_qty: float
    remaining_qty: float
    avg_price: Optional[float]
    create_time: int
    update_time: int


class PositionResponse(BaseModel):
    """持仓响应"""
    symbol: str
    side: str
    size: float
    entry_price: float
    mark_price: float
    unrealized_pnl: float
    realized_pnl: float
    margin: float
    percentage: float
    timestamp: int


class CancelOrderRequest(BaseModel):
    """取消订单请求"""
    symbol: str
    order_id: str
    exchange_type: str = "spot"


def _convert_balance_to_response(balance: Balance) -> BalanceResponse:
    """转换Balance对象为响应格式"""
    return BalanceResponse(
        asset=balance.asset,
        free=balance.free,
        locked=balance.locked,
        total=balance.total
    )


def _convert_order_to_response(order: Order) -> OrderResponse:
    """转换Order对象为响应格式"""
    return OrderResponse(
        id=order.id,
        client_order_id=order.client_order_id,
        symbol=order.symbol,
        side=order.side.value,
        type=order.type.value,
        qty=order.qty,
        price=order.price,
        status=order.status.value,
        filled_qty=order.filled_qty,
        remaining_qty=order.remaining_qty,
        avg_price=order.avg_price,
        create_time=order.create_time,
        update_time=order.update_time
    )


def _convert_position_to_response(position: Position) -> PositionResponse:
    """转换Position对象为响应格式"""
    return PositionResponse(
        symbol=position.symbol,
        side=position.side,
        size=position.size,
        entry_price=position.entry_price,
        mark_price=position.mark_price,
        unrealized_pnl=position.unrealized_pnl,
        realized_pnl=position.realized_pnl,
        margin=position.margin,
        percentage=position.percentage,
        timestamp=position.timestamp
    )


def _validate_order_request(request: OrderRequest) -> tuple:
    """验证订单请求参数"""
    # 验证交易类型
    try:
        exchange_type = ExchangeType(request.exchange_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的交易类型: {request.exchange_type}")
    
    # 验证订单方向
    try:
        side = OrderSide(request.side)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的订单方向: {request.side}")
    
    # 验证订单类型
    try:
        order_type = OrderType(request.type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的订单类型: {request.type}")
    
    # 验证价格参数
    if order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and request.price is None:
        raise HTTPException(status_code=400, detail="限价单和止损限价单必须指定价格")
    
    # 验证数量
    if request.qty <= 0:
        raise HTTPException(status_code=400, detail="订单数量必须大于0")
    
    return exchange_type, side, order_type


@router.get("/account/{exchange_name}", response_model=Dict[str, Any])
async def get_account_info(
    exchange_name: str,
    exchange_type: str = Query("spot", description="交易类型: spot, futures")
):
    """获取账户信息"""
    try:
        # 验证交易类型
        try:
            ex_type = ExchangeType(exchange_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的交易类型: {exchange_type}")
        
        # 获取默认交易所实例
        async with exchange_pool.get_default_exchange_context(exchange_name) as exchange:
            account_info = await exchange.get_account_info(ex_type)
            return account_info
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取账户信息失败: {str(e)}")


@router.get("/balances/{exchange_name}", response_model=List[BalanceResponse])
async def get_balances(
    exchange_name: str,
    exchange_type: str = Query("spot", description="交易类型: spot, futures")
):
    """获取账户余额"""
    try:
        # 验证交易类型
        try:
            ex_type = ExchangeType(exchange_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的交易类型: {exchange_type}")
        
        # 获取默认交易所实例
        async with exchange_pool.get_default_exchange_context(exchange_name) as exchange:
            balances = await exchange.get_balances(ex_type)
            return [_convert_balance_to_response(balance) for balance in balances]
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取账户余额失败: {str(e)}")


@router.post("/orders/{exchange_name}", response_model=OrderResponse)
async def create_order(exchange_name: str, request: OrderRequest):
    """创建订单"""
    try:
        # 验证请求参数
        exchange_type, side, order_type = _validate_order_request(request)
        
        # 获取默认交易所实例
        async with exchange_pool.get_default_exchange_context(exchange_name) as exchange:
            order = await exchange.create_order(
                symbol=request.symbol,
                side=side,
                order_type=order_type,
                qty=request.qty,
                price=request.price,
                client_order_id=request.client_order_id,
                exchange_type=exchange_type
            )
            return _convert_order_to_response(order)
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建订单失败: {str(e)}")


@router.delete("/orders/{exchange_name}", response_model=OrderResponse)
async def cancel_order(exchange_name: str, request: CancelOrderRequest):
    """取消订单"""
    try:
        # 验证交易类型
        try:
            exchange_type = ExchangeType(request.exchange_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的交易类型: {request.exchange_type}")
        
        # 获取默认交易所实例
        async with exchange_pool.get_default_exchange_context(exchange_name) as exchange:
            order = await exchange.cancel_order(
                symbol=request.symbol,
                order_id=request.order_id,
                exchange_type=exchange_type
            )
            return _convert_order_to_response(order)
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消订单失败: {str(e)}")


@router.get("/orders/{exchange_name}/{order_id}", response_model=OrderResponse)
async def get_order(
    exchange_name: str,
    order_id: str,
    symbol: str = Query(..., description="交易对"),
    exchange_type: str = Query("spot", description="交易类型: spot, futures")
):
    """获取订单信息"""
    try:
        # 验证交易类型
        try:
            ex_type = ExchangeType(exchange_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的交易类型: {exchange_type}")
        
        # 获取默认交易所实例
        async with exchange_pool.get_default_exchange_context(exchange_name) as exchange:
            order = await exchange.get_order(symbol, order_id, ex_type)
            return _convert_order_to_response(order)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取订单信息失败: {str(e)}")


@router.get("/orders/{exchange_name}", response_model=List[OrderResponse])
async def get_open_orders(
    exchange_name: str,
    symbol: Optional[str] = Query(None, description="交易对（可选）"),
    exchange_type: str = Query("spot", description="交易类型: spot, futures")
):
    """获取未成交订单"""
    try:
        # 验证交易类型
        try:
            ex_type = ExchangeType(exchange_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的交易类型: {exchange_type}")
        
        # 获取默认交易所实例
        async with exchange_pool.get_default_exchange_context(exchange_name) as exchange:
            orders = await exchange.get_open_orders(symbol, ex_type)
            return [_convert_order_to_response(order) for order in orders]
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取未成交订单失败: {str(e)}")


@router.get("/orders/{exchange_name}/history", response_model=List[OrderResponse])
async def get_order_history(
    exchange_name: str,
    symbol: Optional[str] = Query(None, description="交易对（可选）"),
    limit: int = Query(100, ge=1, le=1000, description="订单数量"),
    exchange_type: str = Query("spot", description="交易类型: spot, futures")
):
    """获取历史订单"""
    try:
        # 验证交易类型
        try:
            ex_type = ExchangeType(exchange_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的交易类型: {exchange_type}")
        
        # 获取默认交易所实例
        async with exchange_pool.get_default_exchange_context(exchange_name) as exchange:
            orders = await exchange.get_order_history(symbol, limit, ex_type)
            return [_convert_order_to_response(order) for order in orders]
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史订单失败: {str(e)}")


@router.get("/positions/{exchange_name}", response_model=List[PositionResponse])
async def get_positions(exchange_name: str):
    """获取持仓信息（期货）"""
    try:
        # 获取默认交易所实例
        async with exchange_pool.get_default_exchange_context(exchange_name) as exchange:
            positions = await exchange.get_positions()
            return [_convert_position_to_response(position) for position in positions]
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotImplementedError:
        raise HTTPException(status_code=400, detail="该交易所不支持期货交易")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取持仓信息失败: {str(e)}")


@router.get("/positions/{exchange_name}/{symbol}", response_model=PositionResponse)
async def get_position(exchange_name: str, symbol: str):
    """获取单个持仓信息（期货）"""
    try:
        # 获取默认交易所实例
        async with exchange_pool.get_default_exchange_context(exchange_name) as exchange:
            position = await exchange.get_position(symbol)
            return _convert_position_to_response(position)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotImplementedError:
        raise HTTPException(status_code=400, detail="该交易所不支持期货交易")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取持仓信息失败: {str(e)}")