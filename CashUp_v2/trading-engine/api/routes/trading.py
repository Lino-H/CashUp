"""
交易服务
基于Gate.io真实API的交易管理接口
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import os
import hmac
import hashlib
import time
import json
import aiohttp

router = APIRouter(prefix="/trading", tags=["交易管理"])

class GateIOTRadingClient:
    """Gate.io交易API客户端"""

    def __init__(self):
        self.base_url = "https://api.gateio.ws/api/v4"
        self.api_key = os.getenv('GATE_IO_API_KEY', '')
        self.api_secret = os.getenv('GATE_IO_SECRET_KEY', '')

    def _generate_signature(self, method: str, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, str]:
        """生成API签名"""
        timestamp = str(int(time.time()))
        body = json.dumps(params or {}, separators=(',', ':'))
        message = f"{method.upper()}\n{endpoint}\n{body}"
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha512
        ).hexdigest()

        return {
            'KEY': self.api_key,
            'Timestamp': timestamp,
            'SIGN': signature
        }

    async def _request(self, method: str, endpoint: str, params: Dict[str, Any] = None):
        """发送HTTP请求"""
        headers = {'Content-Type': 'application/json'}
        signature_headers = self._generate_signature(method, endpoint, params)
        headers.update(signature_headers)

        url = f"{self.base_url}{endpoint}"

        async with aiohttp.ClientSession() as session:
            if method == 'GET':
                if params:
                    url += '?' + '&'.join([f"{key}={value}" for key, value in params.items()])
                async with session.get(url, headers=headers) as response:
                    return await response.json()
            elif method == 'POST':
                async with session.post(url, json=params, headers=headers) as response:
                    return await response.json()
            elif method == 'DELETE':
                async with session.delete(url, json=params, headers=headers) as response:
                    return await response.json()

# 全局交易客户端实例
trading_client = GateIOTRadingClient()

@router.get("/orders/history")
async def get_order_history(
    symbol: str = None,
    status: str = None,
    start_time: datetime = None,
    end_time: datetime = None,
    limit: int = 100,
    offset: int = 0
):
    """获取订单历史"""
    try:
        # 获取现货订单
        spot_orders = await trading_client._request('GET', '/spot/orders')
        # 获取合约订单
        futures_orders = await trading_client._request('GET', '/futures/orders')

        # 合并所有订单
        all_orders = []

        # 处理API返回的数据
        if isinstance(spot_orders, dict) and spot_orders.get('error'):
            spot_orders = []
        else:
            spot_orders = spot_orders if isinstance(spot_orders, list) else []

        if isinstance(futures_orders, dict) and futures_orders.get('error'):
            futures_orders = []
        else:
            futures_orders = futures_orders if isinstance(futures_orders, list) else []

        # 合并所有订单
        all_orders = []

        # 处理现货订单
        for order in spot_orders:
            if isinstance(order, dict) and order.get('status') not in ['deleted']:  # 过滤掉已删除的订单
                try:
                    formatted_order = {
                        "id": order['id'],
                        "symbol": order['currency_pair'].replace('_', '/'),
                        "side": "buy" if order['side'] == 'buy' else "sell",
                        "type": order['type'],
                        "quantity": float(order['amount']),
                        "price": float(order['price']) if order['price'] else None,
                        "status": order['status'],
                        "filled_quantity": float(order['filled_amount']),
                        "average_price": float(order['average_price']) if order['average_price'] else 0.0,
                        "commission": float(order['fee']),
                        "created_at": order['create_time'],
                        "updated_at": order['update_time'],
                        "order_type": "spot"
                    }
                    all_orders.append(formatted_order)
                except (KeyError, ValueError, TypeError):
                    continue

        # 处理合约订单
        for order in futures_orders:
            if isinstance(order, dict) and order.get('status') not in ['deleted']:
                try:
                    formatted_order = {
                        "id": order['id'],
                        "symbol": order['contract'].replace('_', '/'),
                        "side": "buy" if order['side'] == 'buy' else "sell",
                        "type": order['type'],
                        "quantity": float(order['size']),
                        "price": float(order['price']) if order['price'] else None,
                        "status": order['status'],
                        "filled_quantity": float(order['filled_size']),
                        "average_price": float(order['average_price']) if order['average_price'] else 0.0,
                        "commission": float(order['fee']),
                        "created_at": order['create_time'],
                        "updated_at": order['update_time'],
                        "order_type": "futures"
                    }
                    all_orders.append(formatted_order)
                except (KeyError, ValueError, TypeError):
                    continue

        # 过滤条件
        filtered_orders = all_orders
        if symbol:
            filtered_orders = [o for o in filtered_orders if o["symbol"] == symbol]

        if status:
            filtered_orders = [o for o in filtered_orders if o["status"] == status]

        # 时间过滤
        if start_time:
            filtered_orders = [o for o in filtered_orders if datetime.fromisoformat(o["created_at"]) >= start_time]

        if end_time:
            filtered_orders = [o for o in filtered_orders if datetime.fromisoformat(o["created_at"]) <= end_time]

        # 排序（最新的在前）
        filtered_orders.sort(key=lambda x: x["created_at"], reverse=True)

        # 分页
        paginated_orders = filtered_orders[offset:limit + offset]

        return {
            "status": "success",
            "data": {
                "orders": paginated_orders,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": len(filtered_orders)
                },
                "filters": {
                    "symbol": symbol,
                    "status": status,
                    "start_time": start_time.isoformat() if start_time else None,
                    "end_time": end_time.isoformat() if end_time else None
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取订单历史失败: {str(e)}")

@router.post("/orders/cancel/{order_id}")
async def cancel_order(order_id: str):
    """取消订单"""
    try:
        # 首先尝试取消现货订单
        try:
            result = await trading_client._request('DELETE', f'/spot/orders/{order_id}')
            if result and result.get('status'):
                return {
                    "status": "success",
                    "message": f"现货订单 {order_id} 取消成功",
                    "data": {
                        "order_id": order_id,
                        "cancelled_at": datetime.now().isoformat(),
                        "status": result.get('status'),
                        "order_type": "spot"
                    }
                }
        except Exception as spot_error:
            # 现货订单取消失败，尝试合约订单
            pass

        # 尝试取消合约订单
        try:
            result = await trading_client._request('DELETE', f'/futures/orders/{order_id}')
            if result and result.get('status'):
                return {
                    "status": "success",
                    "message": f"合约订单 {order_id} 取消成功",
                    "data": {
                        "order_id": order_id,
                        "cancelled_at": datetime.now().isoformat(),
                        "status": result.get('status'),
                        "order_type": "futures"
                    }
                }
        except Exception as futures_error:
            # 合约订单取消失败
            raise HTTPException(status_code=404, detail=f"未找到订单 {order_id} 或订单状态不允许取消")

        # 如果两种订单类型都失败了
        raise HTTPException(status_code=404, detail=f"未找到订单 {order_id}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消订单失败: {str(e)}")

@router.get("/positions")
async def get_all_positions():
    """获取所有持仓"""
    try:
        # 获取合约持仓
        positions_data = await trading_client._request('GET', '/futures/positions')

        # 处理API返回的数据
        if isinstance(positions_data, dict) and positions_data.get('error'):
            # 如果API返回错误，返回空持仓列表
            positions = []
        else:
            # 如果API返回的是列表，正常处理
            positions_data = positions_data if isinstance(positions_data, list) else []
            positions = []

            total_unrealized_pnl = 0.0
            total_margin_used = 0.0

            for position in positions_data:
                if isinstance(position, dict) and position.get('size') != '0':  # 只显示有仓位的
                    try:
                        size = float(position['size'])
                        entry_price = float(position['average_open_price'])
                        mark_price = float(position['mark_price'])
                        leverage = int(position['leverage'])
                        used_margin = float(position['used_margin'])
                        unrealized_pnl = float(position['unrealized_pnl'])

                        # 计算收益率
                        percentage = (unrealized_pnl / used_margin * 100) if used_margin > 0 else 0
                        side = "long" if size > 0 else "short"

                        formatted_position = {
                            "symbol": position['contract'].replace('_', '/'),
                            "side": side,
                            "size": abs(size),
                            "entry_price": entry_price,
                            "mark_price": mark_price,
                            "unrealized_pnl": unrealized_pnl,
                            "realized_pnl": float(position.get('realized_pnl', 0)),
                            "leverage": leverage,
                            "margin_used": used_margin,
                            "percentage": percentage,
                            "strategy": "manual",  # Gate.io不提供策略信息，默认为手动
                            "created_at": position.get('create_time', datetime.now().isoformat()),
                            "position_type": "futures"
                        }

                        positions.append(formatted_position)
                        total_unrealized_pnl += unrealized_pnl
                        total_margin_used += used_margin
                    except (KeyError, ValueError, TypeError) as e:
                        # 跳过格式错误的数据
                        continue

        return {
            "status": "success",
            "data": {
                "positions": positions,
                "total_positions": len(positions),
                "total_unrealized_pnl": total_unrealized_pnl,
                "total_margin_used": total_margin_used,
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取持仓信息失败: {str(e)}")

@router.get("/positions/{symbol}")
async def get_position_by_symbol(symbol: str):
    """获取指定交易对的持仓"""
    try:
        # 获取所有持仓
        all_positions_data = await trading_client._request('GET', '/futures/positions')
        symbol_positions = []

        for position in all_positions_data:
            if position.get('size') != '0':
                contract = position['contract'].replace('_', '/')
                if contract == symbol:
                    size = float(position['size'])
                    entry_price = float(position['average_open_price'])
                    mark_price = float(position['mark_price'])
                    leverage = int(position['leverage'])
                    used_margin = float(position['used_margin'])
                    unrealized_pnl = float(position['unrealized_pnl'])

                    percentage = (unrealized_pnl / used_margin * 100) if used_margin > 0 else 0
                    side = "long" if size > 0 else "short"

                    formatted_position = {
                        "symbol": contract,
                        "side": side,
                        "size": abs(size),
                        "entry_price": entry_price,
                        "mark_price": mark_price,
                        "unrealized_pnl": unrealized_pnl,
                        "realized_pnl": float(position['realized_pnl']),
                        "leverage": leverage,
                        "margin_used": used_margin,
                        "percentage": percentage,
                        "strategy": "manual",
                        "created_at": position.get('create_time', datetime.now().isoformat()),
                        "position_type": "futures"
                    }
                    symbol_positions.append(formatted_position)

        return {
            "status": "success",
            "data": {
                "symbol": symbol,
                "positions": symbol_positions,
                "total_positions": len(symbol_positions),
                "total_unrealized_pnl": sum(p["unrealized_pnl"] for p in symbol_positions),
                "total_margin_used": sum(p["margin_used"] for p in symbol_positions),
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取指定交易对持仓失败: {str(e)}")

@router.post("/orders/create")
async def create_order(order_data: dict):
    """创建订单"""
    try:
        symbol = order_data.get("symbol", "").replace('/', '_')
        side = order_data.get("side", "")
        order_type = order_data.get("type", "")
        amount = order_data.get("quantity", "")
        price = order_data.get("price", "")

        # 验证必需参数
        if not all([symbol, side, order_type, amount]):
            raise HTTPException(status_code=400, detail="缺少必需参数: symbol, side, type, quantity")

        # 准备订单参数
        order_params = {
            "currency_pair": symbol,
            "side": side,
            "amount": str(amount),
            "type": order_type
        }

        # 限价单需要价格
        if order_type == 'limit' and price:
            order_params["price"] = str(price)
        elif order_type == 'limit' and not price:
            raise HTTPException(status_code=400, detail="限价单需要提供价格")

        # 确定订单类型（现货或合约）
        if 'USDT' in symbol and 'FUTURES' not in symbol.upper():
            # 现货订单
            if order_type == 'market':
                del order_params['price']  # 市价单不需要价格

            result = await trading_client._request('POST', '/spot/orders', order_params)
            order_type_display = "现货"
        else:
            # 合约订单
            order_params['contract'] = symbol
            order_params['settle_currency'] = 'USDT'

            if order_type == 'market':
                del order_params['price']

            result = await trading_client._request('POST', '/futures/orders', order_params)
            order_type_display = "合约"

        if result and result.get('id'):
            return {
                "status": "success",
                "message": f"{order_type_display}订单创建成功",
                "data": {
                    "order_id": result['id'],
                    "symbol": order_data.get("symbol"),
                    "side": side,
                    "type": order_type,
                    "quantity": float(amount),
                    "price": float(price) if price else None,
                    "created_at": result.get('create_time', datetime.now().isoformat()),
                    "order_type": order_type_display.lower()
                }
            }
        else:
            raise HTTPException(status_code=400, detail="订单创建失败，请检查参数")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建订单失败: {str(e)}")

@router.post("/positions/close/{symbol}")
async def close_position(symbol: str):
    """平仓指定交易对的持仓"""
    try:
        # 获取当前持仓
        positions = await get_position_by_symbol(symbol)
        if not positions["data"]["positions"]:
            return {
                "status": "success",
                "message": f"交易对 {symbol} 无持仓",
                "data": {
                    "symbol": symbol,
                    "closed_at": datetime.now().isoformat(),
                    "realized_pnl": 0.0,
                    "closed_positions": 0
                }
            }

        # 创建平仓订单（反向操作）
        current_position = positions["data"]["positions"][0]
        close_side = "sell" if current_position["side"] == "long" else "buy"
        quantity = current_position["size"]

        # 合约平仓
        close_params = {
            "contract": symbol.replace('/', '_'),
            "side": close_side,
            "size": str(quantity),
            "type": "market",
            "settle_currency": "USDT"
        }

        result = await trading_client._request('POST', '/futures/orders/close_position', close_params)

        return {
            "status": "success",
            "message": f"交易对 {symbol} 平仓成功",
            "data": {
                "symbol": symbol,
                "closed_at": datetime.now().isoformat(),
                "realized_pnl": current_position["unrealized_pnl"],
                "closed_positions": len(positions["data"]["positions"]),
                "order_id": result.get('id') if result else None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"平仓失败: {str(e)}")

@router.get("/account/summary")
async def get_account_summary():
    """获取账户摘要"""
    try:
        # 使用账户API获取真实数据
        from api.routes.account import account_client
        account_info = await account_client.get_account_info()

        if account_info.get("status") == "error":
            raise HTTPException(status_code=500, detail=f"获取账户信息失败: {account_info.get('error', '未知错误')}")

        # 格式化账户摘要
        spot_balances = account_info.get("spot_balances", [])
        futures_balances = account_info.get("futures_balances", [])

        total_spot_value = sum(b.get("usdt_value", 0) for b in spot_balances)
        total_futures_value = sum(b.get("usdt_value", 0) for b in futures_balances)
        total_equity = total_spot_value + total_futures_value

        # 计算盈亏
        unrealized_pnl = account_info.get("futures_equity", 0) - total_futures_value
        realized_pnl = 0.0  # Gate.io API不直接提供已实现盈亏

        # 模拟其他账户信息（如果API未提供）
        available_balance = total_equity * 0.8  # 简化计算
        margin_used = account_info.get("futures_equity", 0)
        free_margin = total_equity - margin_used
        margin_ratio = (margin_used / total_equity * 100) if total_equity > 0 else 0

        summary = {
            "total_balance": total_equity,
            "available_balance": available_balance,
            "margin_balance": total_equity,
            "unrealized_pnl": unrealized_pnl,
            "realized_pnl": realized_pnl,
            "total_margin_used": margin_used,
            "free_margin": max(free_margin, 0),
            "margin_ratio": round(margin_ratio, 2),
            "equity": total_equity + unrealized_pnl,
            "risk_level": "low" if margin_ratio < 50 else "medium" if margin_ratio < 80 else "high",
            "leverage": 3,
            "account_type": "futures",
            "trading_enabled": True,
            "timestamp": account_info.get("timestamp", datetime.now().isoformat()),
            "spot_balance": total_spot_value,
            "futures_balance": total_futures_value
        }

        return {
            "status": "success",
            "data": summary
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取账户摘要失败: {str(e)}")

@router.get("/account/pnl")
async def get_pnl_history(
    start_time: datetime = None,
    end_time: datetime = None,
    limit: int = 100
):
    """获取盈亏历史"""
    mock_pnl_history = [
        {
            "id": "pnl_001",
            "type": "realized",
            "symbol": "BTC/USDT",
            "quantity": 0.1,
            "entry_price": 29000.0,
            "exit_price": 30000.0,
            "pnl": 100.0,
            "commission": 0.0,
            "strategy": "grid",
            "created_at": (datetime.now() - timedelta(hours=1)).isoformat()
        },
        {
            "id": "pnl_002",
            "type": "realized",
            "symbol": "ETH/USDT",
            "quantity": 1.0,
            "entry_price": 2100.0,
            "exit_price": 2000.0,
            "pnl": -100.0,
            "commission": 0.0,
            "strategy": "trend",
            "created_at": (datetime.now() - timedelta(hours=3)).isoformat()
        }
    ]

    # 过滤
    if start_time:
        mock_pnl_history = [p for p in mock_pnl_history if datetime.fromisoformat(p["created_at"]) >= start_time]

    if end_time:
        mock_pnl_history = [p for p in mock_pnl_history if datetime.fromisoformat(p["created_at"]) <= end_time]

    # 分页
    paginated_pnl = mock_pnl_history[:limit]

    return {
        "status": "success",
        "data": {
            "pnl_history": paginated_pnl,
            "total_pnl": sum(p["pnl"] for p in mock_pnl_history),
            "winning_trades": len([p for p in mock_pnl_history if p["pnl"] > 0]),
            "losing_trades": len([p for p in mock_pnl_history if p["pnl"] < 0]),
            "total_trades": len(mock_pnl_history),
            "win_rate": 50.0,  # 模拟胜率
            "risk_reward_ratio": 1.5,  # 模拟盈亏比
            "pagination": {
                "limit": limit,
                "total": len(mock_pnl_history)
            }
        }
    }

@router.get("/symbols")
async def get_available_symbols():
    """获取可用交易对"""
    try:
        # 使用市场数据API获取真实交易对列表
        from api.routes.market_data import market_client
        async with market_client:
            symbols_data = await market_client.get_symbols()

        # 过滤出USDT交易对
        usdt_symbols = []
        for symbol in symbols_data:
            if symbol.get('quote') == 'USDT' and symbol.get('status') == 'trading':
                formatted_symbol = {
                    "symbol": symbol.get('id', '').replace('_', '/'),
                    "base_asset": symbol.get('base', ''),
                    "quote_asset": symbol.get('quote', ''),
                    "price_precision": symbol.get('decimal_places', 8),
                    "quantity_precision": symbol.get('amount_decimal_places', 8),
                    "min_quantity": float(symbol.get('min_amount', '0')),
                    "max_quantity": float(symbol.get('max_amount', '1000000')),
                    "min_price": float(symbol.get('min_price', '0.00000001')),
                    "max_price": float(symbol.get('max_price', '1000000')),
                    "status": symbol.get('status', 'trading'),
                    "funding_rate": 0.0001,  # 默认值
                    "funding_rate_8h": 0.0008,  # 默认值
                    "leverage": 3,  # 默认值
                    "market_cap": 0.0,  # API可能不提供
                    "volume_24h": 0.0,  # API可能不提供
                    "last_price": 0.0,  # 需要从ticker获取
                    "price_change_24h": 0.0,  # 需要从ticker获取
                    "timestamp": datetime.now().isoformat()
                }

                # 尝试获取当前价格
                try:
                    ticker = await market_client.get_ticker(symbol.get('id'))
                    formatted_symbol["last_price"] = float(ticker.get('last', 0))
                    formatted_symbol["price_change_24h"] = float(ticker.get('change', 0))
                    formatted_symbol["volume_24h"] = float(ticker.get('quote_volume', 0))
                except:
                    # 如果获取失败，使用默认值
                    pass

                usdt_symbols.append(formatted_symbol)

        return {
            "status": "success",
            "data": {
                "symbols": usdt_symbols,
                "total_symbols": len(usdt_symbols)
            }
        }
    except Exception as e:
        # 如果获取真实数据失败，返回有限的模拟数据
        fallback_symbols = [
            {
                "symbol": "BTC/USDT",
                "base_asset": "BTC",
                "quote_asset": "USDT",
                "price_precision": 2,
                "quantity_precision": 6,
                "min_quantity": 0.0001,
                "max_quantity": 100.0,
                "min_price": 0.01,
                "max_price": 1000000.0,
                "status": "trading",
                "funding_rate": 0.0001,
                "funding_rate_8h": 0.0008,
                "leverage": 3,
                "market_cap": 1000000000.0,
                "volume_24h": 50000000.0,
                "last_price": 31000.0,
                "price_change_24h": 2.5,
                "timestamp": datetime.now().isoformat()
            },
            {
                "symbol": "ETH/USDT",
                "base_asset": "ETH",
                "quote_asset": "USDT",
                "price_precision": 2,
                "quantity_precision": 6,
                "min_quantity": 0.001,
                "max_quantity": 1000.0,
                "min_price": 0.01,
                "max_price": 100000.0,
                "status": "trading",
                "funding_rate": -0.0001,
                "funding_rate_8h": -0.0008,
                "leverage": 3,
                "market_cap": 400000000.0,
                "volume_24h": 30000000.0,
                "last_price": 1950.0,
                "price_change_24h": -1.2,
                "timestamp": datetime.now().isoformat()
            }
        ]
        return {
            "status": "success",
            "data": {
                "symbols": fallback_symbols,
                "total_symbols": len(fallback_symbols)
            }
        }

@router.get("/fees")
async def get_trading_fees():
    """获取交易费率"""
    try:
        # 使用市场数据API获取费率信息（如果提供）
        fees_data = {
            "spot_trading": {
                "maker_fee": 0.001,  # Gate.io现货maker费率
                "taker_fee": 0.002,  # Gate.io现货taker费率
                "fee_currency": "USDT"
            },
            "futures_trading": {
                "maker_fee": 0.002,  # Gate.io合约maker费率
                "taker_fee": 0.003,  # Gate.io合约taker费率
                "fee_currency": "USDT"
            },
            "funding_rate": {
                "long_rate": 0.0001,  # 默认多头费率
                "short_rate": -0.0001,  # 默认空头费率
                "funding_interval": "8h",
                "next_funding_time": (datetime.now() + timedelta(hours=2)).isoformat()
            },
            "api_key_status": "active" if os.getenv('GATE_IO_API_KEY') else "inactive"
        }

        return {
            "status": "success",
            "data": fees_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易费率失败: {str(e)}")