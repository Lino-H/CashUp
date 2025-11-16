"""
Gate.io交易所客户端 - 支持现货和永续合约交易
"""

import asyncio
import aiohttp
import hmac
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import os

from .base import (
    ExchangeBase, ExchangeAdapter, ExchangeManager,
    Ticker, Balance, Order, Trade, Kline, OrderRequest, CancelOrderRequest,
    OrderSide, OrderType, OrderStatus, TimeInForce, ContractType, PositionSide,
    Position, FundingRate
)

class GateIOExchange(ExchangeBase):
    """Gate.io交易所客户端"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # API端点配置
        self.spot_base_url = "https://api.gateio.ws"
        self.futures_base_url = "https://api.gateio.ws/api/v4"
        self.ws_base_url = "wss://ws.gate.io"

        # 测试环境
        if self.sandbox:
            self.spot_base_url = "https://fx-api-testnet.gateio.ws"
            self.futures_base_url = "https://fx-api-testnet.gateio.ws/api/v4"
            self.ws_base_url = "wss://fx-ws-testnet.gateio.ws"

        # 从配置或环境变量获取API密钥
        self.api_key = config.get('api_key', '')
        self.api_secret = config.get('api_secret', '')

        # 如果配置中没有API密钥，尝试从配置服务获取
        if not self.api_key or not self.api_secret:
            try:
                from ..services.config_service import ConfigService
                config_service = ConfigService()
                # 初始化配置服务（同步）
                config_service.initialize()
                credentials = config_service.get_api_credentials('gateio')
                if credentials:
                    self.api_key = credentials.get('api_key', '')
                    self.api_secret = credentials.get('api_secret', '')
            except:
                # 如果配置服务不可用，回退到环境变量
                if not self.api_key:
                    self.api_key = os.getenv('GATE_IO_API_KEY', '')
                if not self.api_secret:
                    self.api_secret = os.getenv('GATE_IO_SECRET_KEY', '')

        self.session = aiohttp.ClientSession()
        self.ws_manager = None
        self.rate_limiter = asyncio.Semaphore(self.rate_limit)

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _generate_signature(self, method: str, endpoint: str, params: Dict[str, Any] = None) -> str:
        """生成API签名"""
        timestamp = str(int(time.time()))
        body = json.dumps(params, separators=(',', ':')) if params else ""
        message = f"{method.upper()}\n{endpoint}\n{body}"
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha512
        ).hexdigest()
        return timestamp, signature

    async def _request(self, method: str, endpoint: str, params: Dict[str, Any] = None,
                      signed: bool = False, use_futures: bool = False) -> Dict[str, Any]:
        """HTTP请求（带UA/超时/重试）"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        async with self.rate_limiter:
            base_url = self.futures_base_url if use_futures else self.spot_base_url
            url = f"{base_url}{endpoint}"

            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'CashUp-Client/2.0 (+https://cashup.example)'
            }

            if signed:
                timestamp, signature = self._generate_signature(method, endpoint, params)
                headers['KEY'] = self.api_key
                headers['Timestamp'] = timestamp
                headers['SIGN'] = signature

            tries = 0
            last_exc: Exception | None = None
            while tries < 3:
                try:
                    timeout = aiohttp.ClientTimeout(total=30)
                    if method == 'GET':
                        async with self.session.get(url, params=params or {}, headers=headers, timeout=timeout) as response:
                            ct = response.headers.get('Content-Type', '')
                            if 'application/json' in ct:
                                return await response.json()
                            text = await response.text()
                            try:
                                import json as _json
                                return _json.loads(text)
                            except Exception:
                                raise ValueError(f"Unexpected content-type: {ct}")
                    elif method == 'POST':
                        async with self.session.post(url, json=params or {}, headers=headers, timeout=timeout) as response:
                            return await response.json()
                    elif method == 'DELETE':
                        async with self.session.delete(url, json=params or {}, headers=headers, timeout=timeout) as response:
                            return await response.json()
                    else:
                        async with self.session.request(method, url, json=params or {}, headers=headers, timeout=timeout) as response:
                            return await response.json()
                except Exception as e:
                    last_exc = e
                    tries += 1
                    await asyncio.sleep(2 ** tries)
            raise last_exc if last_exc else RuntimeError("request failed")

    # 现货交易方法
    async def get_ticker(self, symbol: str) -> Ticker:
        """获取现货行情"""
        gate_symbol = symbol.replace('/', '_')
        endpoint = f"/api/v4/spot/tickers"
        params = {'currency_pair': gate_symbol}

        data = await self._request('GET', endpoint, params)

        if data and len(data) > 0:
            item = data[0]
            return Ticker(
                symbol=item['currency_pair'].replace('_', '/'),
                last_price=float(item['last']),
                bid_price=float(item['highest_bid']),
                ask_price=float(item['lowest_ask']),
                bid_volume=0.0,
                ask_volume=0.0,
                volume_24h=float(item['base_volume']),
                high_24h=float(item['high_24h']),
                low_24h=float(item['low_24h']),
                price_change_24h=0.0,  # Gate.io API中不提供24h价格变化
                price_change_percent_24h=float(item.get('change_percentage', 0)),
                timestamp=datetime.now()
            )
        else:
            raise ValueError(f"获取不到 {symbol} 的行情数据")

    async def get_klines(self, symbol: str, interval: str,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        limit: int = 100) -> List[Kline]:
        """获取K线数据"""
        gate_symbol = symbol.replace('/', '_')
        endpoint = f"/api/v4/spot/candlesticks"

        interval_map = {
            '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m',
            '1h': '1h', '4h': '4h', '8h': '8h', '1d': '1d',
            '7d': '7d'
        }
        gate_interval = interval_map.get(interval, '1h')

        params = {
            'currency_pair': gate_symbol,
            'interval': gate_interval,
            'limit': min(limit, 1000)
        }

        if start_time:
            params['from'] = int(start_time.timestamp())

        if end_time:
            params['to'] = int(end_time.timestamp())

        data = await self._request('GET', endpoint, params)

        klines: List[Kline] = []
        for item in data:
            # Gate.io candlesticks: [t, volume, close, high, low, open, quote_volume]
            ts = int(item[0])
            kline = Kline(
                symbol=symbol,
                interval=interval,
                open_time=datetime.fromtimestamp(ts),
                close_time=datetime.fromtimestamp(ts + self.get_interval_minutes(interval) * 60),
                open_price=float(item[5]),
                high_price=float(item[3]),
                low_price=float(item[4]),
                close_price=float(item[2]),
                volume=float(item[1]),
                quote_volume=float(item[6]),
                trades_count=0,
                taker_buy_volume=0.0,
                taker_buy_quote_volume=0.0
            )
            klines.append(kline)

        return klines

    async def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """获取订单簿"""
        gate_symbol = symbol.replace('/', '_')
        endpoint = f"/api/v4/spot/order_book"
        params = {'currency_pair': gate_symbol, 'limit': limit}

        return await self._request('GET', endpoint, params)

    async def get_balance(self) -> Dict[str, Balance]:
        """获取现货账户余额"""
        endpoint = f"/api/v4/spot/accounts"
        data = await self._request('GET', endpoint, signed=True)

        balances = {}
        for item in data:
            if item['available'] != '0' or item['locked'] != '0':
                balances[item['currency']] = Balance(
                    asset=item['currency'],
                    free=float(item['available']),
                    used=float(item['locked']),
                    total=float(item['available']) + float(item['locked'])
                )

        return balances

    async def get_orders(self, symbol: Optional[str] = None,
                        status: Optional[OrderStatus] = None) -> List[Order]:
        """获取订单列表"""
        endpoint = f"/api/v4/spot/orders"
        params = {}

        if symbol:
            params['currency_pair'] = symbol.replace('/', '_')

        if status:
            status_map = {
                OrderStatus.OPEN: 'open',
                OrderStatus.FILLED: 'finished',
                OrderStatus.CANCELLED: 'cancelled'
            }
            params['status'] = status_map.get(status, 'open')

        data = await self._request('GET', endpoint, params, signed=True)

        orders = []
        for item in data:
            order = Order(
                id=str(item['id']),
                client_order_id=item.get('text'),
                symbol=item['currency_pair'].replace('_', '/'),
                side=OrderSide(item['side'].lower()),
                type=self._map_order_type(item['type']),
                quantity=float(item['amount']),
                price=float(item['price']) if item['price'] else None,
                stop_price=None,
                time_in_force=TimeInForce.GTC,
                status=self._map_order_status(item['status']),
                filled_quantity=float(item['filled']),
                remaining_quantity=float(item['left']),
                average_price=float(item['fill_price']) if item['fill_price'] else None,
                commission=0.0,
                created_at=datetime.fromtimestamp(item['create_time']),
                updated_at=datetime.fromtimestamp(item['update_time']),
                exchange='gateio'
            )
            orders.append(order)

        return orders

    async def place_order(self, request: OrderRequest) -> Order:
        """下单"""
        if not self.validate_order_request(request):
            raise ValueError("无效的下单请求")

        gate_symbol = request.symbol.replace('/', '_')
        endpoint = f"/api/v4/spot/orders"

        params = {
            'currency_pair': gate_symbol,
            'side': request.side.value,
            'amount': str(request.quantity),
            'type': self._reverse_map_order_type(request.type)
        }

        if request.price:
            params['price'] = str(request.price)

        if request.client_order_id:
            params['text'] = request.client_order_id

        data = await self._request('POST', endpoint, params, signed=True)

        return Order(
            id=str(data['id']),
            client_order_id=data.get('text'),
            symbol=data['currency_pair'].replace('_', '/'),
            side=request.side,
            type=request.type,
            quantity=float(data['amount']),
            price=float(data['price']) if data['price'] else None,
            stop_price=None,
            time_in_force=request.time_in_force,
            status=self._map_order_status(data['status']),
            filled_quantity=float(data['filled']),
            remaining_quantity=float(data['left']),
            average_price=float(data['fill_price']) if data['fill_price'] else None,
            commission=0.0,
            created_at=datetime.fromtimestamp(data['create_time']),
            updated_at=datetime.fromtimestamp(data['update_time']),
            exchange='gateio'
        )

    # 永续合约方法
    async def get_futures_balance(self) -> Dict[str, Balance]:
        """获取永续合约账户余额"""
        endpoint = f"/api/v4/futures/accounts"
        data = await self._request('GET', endpoint, signed=True, use_futures=True)

        balances = {}
        for item in data:
            if item['available_balance'] != '0' or item['used_margin'] != '0':
                balances[item['currency']] = Balance(
                    asset=item['currency'],
                    free=float(item['available_balance']),
                    used=float(item['used_margin']),
                    total=float(item['available_balance']) + float(item['used_margin'])
                )

        return balances

    async def get_futures_positions(self, symbol: Optional[str] = None) -> List[Position]:
        """获取永续合约持仓"""
        endpoint = f"/api/v4/futures/positions"
        params = {}

        if symbol:
            params['settle_currency'] = symbol.split('/')[0]  # 例如 ETH/USDT -> ETH

        data = await self._request('GET', endpoint, params, signed=True, use_futures=True)

        positions = []
        for item in data:
            if item.size != '0':  # 只返回有持仓的
                position = Position(
                    symbol=item['contract'],
                    side=PositionSide.LONG if float(item.size) > 0 else PositionSide.SHORT,
                    size=float(item.size),
                    entry_price=float(item['average_open_price']),
                    mark_price=float(item['mark_price']),
                    liquidation_price=float(item['liquidation_price']),
                    unrealized_pnl=float(item['unrealized_pnl']),
                    realized_pnl=float(item['realized_pnl']),
                    leverage=int(item['leverage']),
                    margin_used=float(item['used_margin']),
                    timestamp=datetime.now(),
                    exchange='gateio'
                )
                positions.append(position)

        return positions

    async def get_funding_rate(self, symbol: str) -> FundingRate:
        """获取资金费率"""
        gate_symbol = symbol.replace('/', '_')
        endpoint = f"/api/v4/futures/funding_rate"
        params = {'contract': gate_symbol}

        data = await self._request('GET', endpoint, params, use_futures=True)

        if data and len(data) > 0:
            item = data[0]
            return FundingRate(
                symbol=symbol,
                funding_rate=float(item['funding_rate']),
                funding_rate_8h=float(item['funding_rate_8h']),
                next_funding_time=datetime.fromtimestamp(item['next_funding_time']),
                mark_price=float(item['mark_price']),
                index_price=float(item['index_price']),
                timestamp=datetime.now(),
                exchange='gateio'
            )
        else:
            raise ValueError(f"获取不到 {symbol} 的资金费率数据")

    async def set_leverage(self, symbol: str, leverage: int) -> bool:
        """设置杠杆"""
        gate_symbol = symbol.replace('/', '_')
        endpoint = f"/api/v4/futures/leverage"
        params = {
            'contract': gate_symbol,
            'leverage': str(leverage)
        }

        try:
            await self._request('POST', endpoint, params, signed=True, use_futures=True)
            return True
        except:
            return False

    # WebSocket相关方法
    async def init_websocket_manager(self):
        """初始化WebSocket管理器"""
        if self.ws_manager is None:
            from .gateio_ws import GateIOWSManager
            self.ws_manager = GateIOWSManager(self.config)
            await self.ws_manager.connect()

    async def subscribe_eth_usdt_data(self, callback):
        """订阅ETHUSDT永续合约数据"""
        if self.ws_manager is None:
            await self.init_websocket_manager()

        await self.ws_manager.subscribe_eth_usdt_perpetual(callback)

    async def subscribe_ticker(self, symbol: str, callback):
        """订阅行情推送"""
        if self.ws_manager is None:
            await self.init_websocket_manager()

        await self.ws_manager.subscribe('ticker', symbol, callback)

    async def subscribe_kline(self, symbol: str, interval: str, callback):
        """订阅K线推送"""
        if self.ws_manager is None:
            await self.init_websocket_manager()

        await self.ws_manager.subscribe('kline', symbol, callback)

    async def subscribe_order_book(self, symbol: str, callback):
        """订阅订单簿推送"""
        if self.ws_manager is None:
            await self.init_websocket_manager()

        await self.ws_manager.subscribe('order_book', symbol, callback)

    async def subscribe_trades(self, symbol: str, callback):
        """订阅成交推送"""
        if self.ws_manager is None:
            await self.init_websocket_manager()

        await self.ws_manager.subscribe('trades', symbol, callback)

    async def subscribe_funding_rate(self, symbol: str, callback):
        """订阅资金费率推送"""
        if self.ws_manager is None:
            await self.init_websocket_manager()

        await self.ws_manager.subscribe('funding_rate', symbol, callback)

    async def subscribe_mark_price(self, symbol: str, callback):
        """订阅标记价格推送"""
        if self.ws_manager is None:
            await self.init_websocket_manager()

        await self.ws_manager.subscribe('ticker', symbol, callback)  # 从ticker中提取

    async def subscribe_liquidation_orders(self, callback):
        """订阅强制平仓推送"""
        if self.ws_manager is None:
            await self.init_websocket_manager()

        await self.ws_manager.subscribe_liquidation_orders(callback)

    async def subscribe_user_data(self, callback):
        """订阅用户数据推送"""
        # TODO: 实现用户数据推送
        pass

    # 辅助方法
    def _map_order_status(self, status: str) -> OrderStatus:
        """映射订单状态"""
        status_map = {
            'open': OrderStatus.OPEN,
            'finished': OrderStatus.FILLED,
            'cancelled': OrderStatus.CANCELLED,
            'matching': OrderStatus.PARTIALLY_FILLED
        }
        return status_map.get(status, OrderStatus.UNKNOWN)

    def _map_order_type(self, order_type: str) -> OrderType:
        """映射订单类型"""
        type_map = {
            'limit': OrderType.LIMIT,
            'market': OrderType.MARKET,
            'post_only': OrderType.POST_ONLY,
            'ioc': OrderType.IOC,
            'fok': OrderType.FOK
        }
        return type_map.get(order_type, OrderType.LIMIT)

    def _reverse_map_order_type(self, order_type: OrderType) -> str:
        """反向映射订单类型"""
        type_map = {
            OrderType.LIMIT: 'limit',
            OrderType.MARKET: 'market',
            OrderType.POST_ONLY: 'post_only',
            OrderType.IOC: 'ioc',
            OrderType.FOK: 'fok'
        }
        return type_map.get(order_type, 'limit')

    def parse_symbol(self, symbol: str) -> Dict[str, str]:
        """解析交易对"""
        parts = symbol.split('_')
        if len(parts) == 2:
            return {'base': parts[0], 'quote': parts[1]}
        else:
            return {'base': '', 'quote': ''}

    def format_symbol(self, base: str, quote: str) -> str:
        """格式化交易对"""
        return f"{base}/{quote}"

    # 添加缺失的抽象方法实现
    async def get_server_time(self) -> datetime:
        """获取服务器时间"""
        endpoint = f"/api/v4/spot/time"
        data = await self._request('GET', endpoint)
        return datetime.fromtimestamp(data['server_time'] / 1000)  # 转换为毫秒

    async def get_symbols(self) -> List[Dict[str, Any]]:
        """获取交易对信息"""
        endpoint = f"/api/v4/spot/currency_pairs"

        data = await self._request('GET', endpoint)

        symbols = []
        for item in data:
            if item['trade_status'] == 'tradable':
                symbols.append({
                    'symbol': item['id'].replace('_', '/'),
                    'base_asset': item['base'],
                    'quote_asset': item['quote'],
                    'min_price': 0.0,  # Gate.io API中不提供最小价格限制
                    'max_price': float('inf'),  # Gate.io API中不提供最大价格限制
                    'tick_size': 10 ** (-int(item.get('precision', 8))),  # 根据精度计算tick size
                    'min_qty': float(item['min_base_amount']) if item.get('min_base_amount') else 0.0,
                    'max_qty': float('inf'),  # Gate.io API中不提供最大数量限制
                    'step_size': 10 ** (-int(item.get('amount_precision', 8))),  # 根据数量精度计算step size
                    'status': item['trade_status']
                })

        return symbols

    async def get_exchange_info(self) -> Dict[str, Any]:
        """获取交易所信息"""
        endpoint = f"/api/v4/spot/currency_pairs"
        data = await self._request('GET', endpoint)
        return {'currency_pairs': data}

    async def cancel_order(self, request: CancelOrderRequest) -> bool:
        """取消订单"""
        gate_symbol = request.symbol.replace('/', '_')
        endpoint = f"/api/v4/spot/orders/{request.order_id}" if request.order_id else f"/api/v4/spot/orders"

        params = {}
        if not request.order_id and request.client_order_id:
            params = {'text': request.client_order_id}

        try:
            await self._request('DELETE', endpoint, params, signed=True)
            return True
        except Exception:
            return False

    async def cancel_all_orders(self, symbol: str) -> List[Order]:
        """取消所有订单"""
        gate_symbol = symbol.replace('/', '_')
        endpoint = f"/api/v4/spot/orders"
        params = {'currency_pair': gate_symbol}

        try:
            data = await self._request('DELETE', endpoint, params, signed=True)

            orders = []
            for item in data:
                order = Order(
                    id=str(item['id']),
                    client_order_id=item.get('text'),
                    symbol=item['currency_pair'].replace('_', '/'),
                    side=OrderSide(item['side'].lower()),
                    type=self._map_order_type(item['type']),
                    quantity=float(item['amount']),
                    price=float(item['price']) if item['price'] else None,
                    stop_price=None,
                    time_in_force=TimeInForce.GTC,
                    status=OrderStatus.CANCELLED,
                    filled_quantity=float(item['filled']),
                    remaining_quantity=float(item['left']),
                    average_price=float(item['fill_price']) if item['fill_price'] else None,
                    commission=0.0,
                    created_at=datetime.fromtimestamp(item['create_time']),
                    updated_at=datetime.fromtimestamp(item['update_time']),
                    exchange='gateio'
                )
                orders.append(order)

            return orders
        except Exception:
            return []

    async def get_order(self, order_id: str, symbol: str) -> Optional[Order]:
        """获取单个订单信息"""
        gate_symbol = symbol.replace('/', '_')
        endpoint = f"/api/v4/spot/orders/{order_id}"

        try:
            data = await self._request('GET', endpoint, signed=True)

            return Order(
                id=str(data['id']),
                client_order_id=data.get('text'),
                symbol=data['currency_pair'].replace('_', '/'),
                side=OrderSide(data['side'].lower()),
                type=self._map_order_type(data['type']),
                quantity=float(data['amount']),
                price=float(data['price']) if data['price'] else None,
                stop_price=None,
                time_in_force=TimeInForce.GTC,
                status=self._map_order_status(data['status']),
                filled_quantity=float(data['filled']),
                remaining_quantity=float(data['left']),
                average_price=float(data['fill_price']) if data['fill_price'] else None,
                commission=0.0,
                created_at=datetime.fromtimestamp(data['create_time']),
                updated_at=datetime.fromtimestamp(data['update_time']),
                exchange='gateio'
            )
        except Exception:
            return None

    async def get_trades(self, symbol: str, order_id: Optional[str] = None,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        limit: int = 100) -> List[Trade]:
        """获取成交记录"""
        gate_symbol = symbol.replace('/', '_')
        endpoint = f"/api/v4/spot/my_trades"
        params = {'currency_pair': gate_symbol, 'limit': limit}

        if order_id:
            params['order_id'] = order_id
        if start_time:
            params['from'] = int(start_time.timestamp())
        if end_time:
            params['to'] = int(end_time.timestamp())

        data = await self._request('GET', endpoint, params, signed=True)

        trades = []
        for item in data:
            trade = Trade(
                id=str(item['id']),
                order_id=str(item['order_id']),
                symbol=item['currency_pair'].replace('_', '/'),
                side=OrderSide(item['side'].lower()),
                quantity=float(item['amount']),
                price=float(item['price']),
                commission=float(item['fee']),
                commission_asset=item['fee_currency'],
                timestamp=datetime.fromtimestamp(item['create_time']),
                exchange='gateio'
            )
            trades.append(trade)

        return trades

    async def set_leverage(self, symbol: str, leverage: int) -> bool:
        """设置杠杆"""
        gate_symbol = symbol.replace('/', '_')
        endpoint = f"/api/v4/futures/leverage"
        params = {
            'contract': gate_symbol,
            'leverage': str(leverage)
        }

        try:
            await self._request('POST', endpoint, params, signed=True, use_futures=True)
            return True
        except:
            return False

    async def get_leverage(self, symbol: str) -> int:
        """获取当前杠杆"""
        gate_symbol = symbol.replace('/', '_')
        endpoint = f"/api/v4/futures/leverage"
        params = {'contract': gate_symbol}

        try:
            data = await self._request('GET', endpoint, params, signed=True, use_futures=True)
            return int(data['leverage'])
        except:
            return 1

    async def get_funding_rate_history(self, symbol: str,
                                     start_time: Optional[datetime] = None,
                                     end_time: Optional[datetime] = None,
                                     limit: int = 100) -> List[FundingRate]:
        """获取资金费率历史"""
        gate_symbol = symbol.replace('/', '_')
        endpoint = f"/api/v4/futures/funding_rate"
        params = {'contract': gate_symbol, 'limit': limit}

        if start_time:
            params['from'] = int(start_time.timestamp())
        if end_time:
            params['to'] = int(end_time.timestamp())

        data = await self._request('GET', endpoint, params, use_futures=True)

        funding_rates = []
        for item in data:
            funding_rate = FundingRate(
                symbol=symbol,
                funding_rate=float(item['funding_rate']),
                funding_rate_8h=float(item['funding_rate_8h']),
                next_funding_time=datetime.fromtimestamp(item['next_funding_time']),
                mark_price=float(item['mark_price']),
                index_price=float(item['index_price']),
                timestamp=datetime.fromtimestamp(item['create_time']),
                exchange='gateio'
            )
            funding_rates.append(funding_rate)

        return funding_rates