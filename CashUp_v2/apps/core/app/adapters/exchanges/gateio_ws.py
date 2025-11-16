"""
Gate.io WebSocket管理器 - 处理实时数据订阅
"""

import asyncio
import json
import websockets
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import logging

from .base import Ticker, Kline, OrderBook, Trade, FundingRate, Position, Order

logger = logging.getLogger(__name__)

class GateIOWSManager:
    """Gate.io WebSocket管理器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = "wss://ws.gate.io" if not config.get('sandbox', False) else "wss://fx-ws-testnet.gateio.ws"
        self.connections: Dict[str, websockets.WebSocketClientProtocol] = {}
        self.subscriptions: Dict[str, List[Callable]] = {}
        self.is_running = False
        self.reconnect_attempts = {}
        self.max_reconnect_attempts = 5

    async def connect(self) -> bool:
        """连接到Gate.io WebSocket"""
        try:
            # 首先建立基础连接
            self.ws = await websockets.connect(self.base_url)
            self.is_running = True
            logger.info("成功连接到Gate.io WebSocket")

            # 启动心跳
            asyncio.create_task(self._heartbeat())
            return True

        except Exception as e:
            logger.error(f"连接Gate.io WebSocket失败: {e}")
            return False

    async def disconnect(self):
        """断开连接"""
        self.is_running = False

        # 关闭所有订阅
        for channel_name, connection in self.connections.items():
            try:
                await connection.close()
            except:
                pass

        # 关闭主连接
        if hasattr(self, 'ws'):
            try:
                await self.ws.close()
            except:
                pass

        logger.info("已断开Gate.io WebSocket连接")

    async def subscribe(self, channel: str, symbol: str, callback: Callable):
        """订阅频道"""
        if not self.is_running:
            await self.connect()

        channel_id = f"{channel}_{symbol}"

        # 存储回调函数
        if channel_id not in self.subscriptions:
            self.subscriptions[channel_id] = []
        self.subscriptions[channel_id].append(callback)

        # 如果连接不存在，建立连接
        if channel_id not in self.connections:
            await self._create_channel_connection(channel, symbol)

        logger.info(f"订阅频道: {channel_id}")

    async def unsubscribe(self, channel: str, symbol: str):
        """取消订阅频道"""
        channel_id = f"{channel}_{symbol}"

        if channel_id in self.subscriptions:
            del self.subscriptions[channel_id]

        if channel_id in self.connections:
            try:
                await self.connections[channel_id].close()
                del self.connections[channel_id]
            except:
                pass

        logger.info(f"取消订阅频道: {channel_id}")

    async def _create_channel_connection(self, channel: str, symbol: str):
        """为特定频道创建WebSocket连接"""
        channel_id = f"{channel}_{symbol}"

        try:
            # 为每个频道创建独立的连接
            ws = await websockets.connect(self.base_url)
            self.connections[channel_id] = ws

            # 订阅频道
            subscribe_msg = self._create_subscribe_message(channel, symbol)
            await ws.send(json.dumps(subscribe_msg))

            # 启动消息处理
            asyncio.create_task(self._handle_channel_messages(channel_id, ws))

        except Exception as e:
            logger.error(f"创建频道连接失败 {channel_id}: {e}")

            # 重连逻辑
            if channel_id not in self.reconnect_attempts:
                self.reconnect_attempts[channel_id] = 0

            if self.reconnect_attempts[channel_id] < self.max_reconnect_attempts:
                self.reconnect_attempts[channel_id] += 1
                delay = min(2 ** self.reconnect_attempts[channel_id], 30)
                logger.info(f"将在 {delay} 秒后重连 {channel_id}")
                asyncio.create_task(self._reconnect_later(channel, symbol, delay))

    def _create_subscribe_message(self, channel: str, symbol: str) -> Dict[str, Any]:
        """创建订阅消息"""
        # 转换符号格式
        gate_symbol = symbol.replace('/', '_')

        if channel == 'ticker':
            return {
                "time": int(datetime.now().timestamp()),
                "channel": f"spot.{gate_symbol}.ticker",
                "event": "subscribe",
                "payload": [f"spot.{gate_symbol}.ticker"]
            }
        elif channel == 'kline':
            # 默认订阅1分钟K线
            return {
                "time": int(datetime.now().timestamp()),
                "channel": f"spot.{gate_symbol}.candlesticks",
                "event": "subscribe",
                "payload": [f"spot.{gate_symbol}.candlesticks_1m"]
            }
        elif channel == 'order_book':
            return {
                "time": int(datetime.now().timestamp()),
                "channel": f"spot.{gate_symbol}.depth",
                "event": "subscribe",
                "payload": [f"spot.{gate_symbol}.depth"]
            }
        elif channel == 'trades':
            return {
                "time": int(datetime.now().timestamp()),
                "channel": f"spot.{gate_symbol}.trades",
                "event": "subscribe",
                "payload": [f"spot.{gate_symbol}.trades"]
            }
        elif channel == 'funding_rate':
            # 永续合约资金费率
            return {
                "time": int(datetime.now().timestamp()),
                "channel": f"futures.{gate_symbol}.funding_rate",
                "event": "subscribe",
                "payload": [f"futures.{gate_symbol}.funding_rate"]
            }
        else:
            raise ValueError(f"不支持的频道类型: {channel}")

    async def _handle_channel_messages(self, channel_id: str, ws: websockets.WebSocketClientProtocol):
        """处理频道消息"""
        try:
            async for message in ws:
                if not self.is_running:
                    break

                try:
                    data = json.loads(message)
                    await self._process_message(channel_id, data)
                except json.JSONDecodeError:
                    logger.warning(f"无法解析JSON消息: {message}")
                except Exception as e:
                    logger.error(f"处理消息失败 {channel_id}: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.warning(f"频道连接已关闭: {channel_id}")
        except Exception as e:
            logger.error(f"频道消息处理异常 {channel_id}: {e}")
        finally:
            if channel_id in self.connections:
                del self.connections[channel_id]

    async def _process_message(self, channel_id: str, data: Dict[str, Any]):
        """处理接收到的消息"""
        channel_name = channel_id.split('_')[0]
        symbol = '_'.join(channel_id.split('_')[1:])

        # 转换回标准符号格式
        symbol = symbol.replace('_', '/')

        callbacks = self.subscriptions.get(channel_id, [])

        try:
            if channel_name == 'ticker':
                ticker_data = self._parse_ticker(data, symbol)
                for callback in callbacks:
                    await callback(ticker_data)

            elif channel_name == 'kline':
                kline_data = self._parse_kline(data, symbol)
                for callback in callbacks:
                    await callback(kline_data)

            elif channel_name == 'order_book':
                orderbook_data = self._parse_orderbook(data, symbol)
                for callback in callbacks:
                    await callback(orderbook_data)

            elif channel_name == 'trades':
                trades_data = self._parse_trades(data, symbol)
                for callback in callbacks:
                    await callback(trades_data)

            elif channel_name == 'funding_rate':
                funding_data = self._parse_funding_rate(data, symbol)
                for callback in callbacks:
                    await callback(funding_data)

        except Exception as e:
            logger.error(f"解析消息失败 {channel_id}: {e}")

    def _parse_ticker(self, data: Dict[str, Any], symbol: str) -> Ticker:
        """解析行情数据"""
        result = data.get('result', {})

        return Ticker(
            symbol=symbol,
            last_price=float(result.get('last', 0)),
            bid_price=float(result.get('highest_bid', 0)),
            ask_price=float(result.get('lowest_ask', 0)),
            bid_volume=0.0,  # Gate.io不提供买卖量数据
            ask_volume=0.0,
            volume_24h=float(result.get('base_volume', 0)),
            high_24h=float(result.get('high_24h', 0)),
            low_24h=float(result.get('low_24h', 0)),
            price_change_24h=float(result.get('change', 0)),
            price_change_percent_24h=float(result.get('change_percentage', 0)),
            timestamp=datetime.now()
        )

    def _parse_kline(self, data: Dict[str, Any], symbol: str) -> Kline:
        """解析K线数据"""
        result = data.get('result', {})

        # K线数据格式: [time, open, high, low, close, volume, quote_volume]
        kline_data = result.get('data', [])[0] if result.get('data') else [0, 0, 0, 0, 0, 0, 0]

        return Kline(
            symbol=symbol,
            interval='1m',  # 当前只支持1分钟线
            open_time=datetime.fromtimestamp(kline_data[0]),
            close_time=datetime.fromtimestamp(kline_data[0] + 60),
            open_price=float(kline_data[1]),
            high_price=float(kline_data[2]),
            low_price=float(kline_data[3]),
            close_price=float(kline_data[4]),
            volume=float(kline_data[5]),
            quote_volume=float(kline_data[6]),
            trades_count=0,
            taker_buy_volume=0.0,
            taker_buy_quote_volume=0.0
        )

    def _parse_orderbook(self, data: Dict[str, Any], symbol: str) -> OrderBook:
        """解析订单簿数据"""
        result = data.get('result', {})

        asks = result.get('asks', [])
        bids = result.get('bids', [])

        return OrderBook(
            symbol=symbol,
            asks=[{'price': float(ask[0]), 'quantity': float(ask[1])} for ask in asks],
            bids=[{'price': float(bid[0]), 'quantity': float(bid[1])} for bid in bids],
            timestamp=datetime.now()
        )

    def _parse_trades(self, data: Dict[str, Any], symbol: str) -> List[Trade]:
        """解析成交数据"""
        result = data.get('result', {})
        trades_data = result.get('data', [])

        trades = []
        for trade_data in trades_data:
            trade = Trade(
                id=str(trade_data.get('id', '')),
                order_id='',
                symbol=symbol,
                side='buy' if trade_data.get('side') == 'buy' else 'sell',
                quantity=float(trade_data.get('amount', 0)),
                price=float(trade_data.get('price', 0)),
                commission=float(trade_data.get('fee', 0)),
                commission_asset='',
                timestamp=datetime.fromtimestamp(trade_data.get('create_time', 0)),
                exchange='gateio'
            )
            trades.append(trade)

        return trades

    def _parse_funding_rate(self, data: Dict[str, Any], symbol: str) -> FundingRate:
        """解析资金费率数据"""
        result = data.get('result', {})

        funding_info = result.get('funding_rate', {})

        return FundingRate(
            symbol=symbol,
            funding_rate=float(funding_info.get('funding_rate', 0)),
            funding_rate_8h=float(funding_info.get('funding_rate_8h', 0)),
            next_funding_time=datetime.fromtimestamp(funding_info.get('next_funding_time', 0)),
            mark_price=float(funding_info.get('mark_price', 0)),
            index_price=float(funding_info.get('index_price', 0)),
            timestamp=datetime.now(),
            exchange='gateio'
        )

    async def _heartbeat(self):
        """心跳保持"""
        if not hasattr(self, 'ws'):
            return

        while self.is_running:
            try:
                heartbeat_msg = {
                    "time": int(datetime.now().timestamp()),
                    "event": "ping"
                }
                await self.ws.send(json.dumps(heartbeat_msg))
                await asyncio.sleep(30)  # 30秒心跳
            except Exception as e:
                logger.error(f"心跳发送失败: {e}")
                break

    async def _reconnect_later(self, channel: str, symbol: str, delay: int):
        """延迟重连"""
        await asyncio.sleep(delay)

        if self.is_running and f"{channel}_{symbol}" in self.subscriptions:
            logger.info(f"重连频道: {channel}_{symbol}")
            await self._create_channel_connection(channel, symbol)

    async def _subscribe_perpetual_data(self, symbol: str, callback: Callable):
        """订阅永续合约数据"""
        # 订阅多个频道
        channels = ['ticker', 'kline', 'order_book', 'trades', 'funding_rate']

        for channel in channels:
            await self.subscribe(channel, symbol, callback)

    # 永续合约特定订阅方法
    async def subscribe_eth_usdt_perpetual(self, callback: Callable):
        """订阅ETHUSDT永续合约数据"""
        symbol = 'ETH/USDT'
        await self._subscribe_perpetual_data(symbol, callback)

    async def subscribe_mark_price(self, symbol: str, callback: Callable):
        """订阅标记价格"""
        # Gate.io的标记价格包含在ticker数据中
        await self.subscribe('ticker', symbol, callback)

    async def subscribe_liquidation_orders(self, callback: Callable):
        """订阅强制平仓推送"""
        # 注意：Gate.io可能不支持专门的强制平仓推送频道
        # 这里可以作为占位符实现
        logger.warning("强制平仓推送功能暂未实现")
        pass