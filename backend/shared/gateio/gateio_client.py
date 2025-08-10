#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - Gate.io API客户端

实现Gate.io REST API和WebSocket API的完整对接
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from urllib.parse import urlencode

import aiohttp
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

logger = logging.getLogger(__name__)


class GateIORestClient:
    """
    Gate.io REST API客户端
    
    支持现货、期货交易的完整API对接
    """
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False,
        timeout: int = 30
    ):
        """
        初始化Gate.io REST客户端
        
        Args:
            api_key: API密钥
            api_secret: API密钥
            testnet: 是否使用测试网
            timeout: 请求超时时间
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.timeout = timeout
        
        # API基础URL
        if testnet:
            self.base_url = "https://api-testnet.gateapi.io/api/v4"
        else:
            self.base_url = "https://api.gateio.ws/api/v4"
        
        # HTTP会话
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
    
    async def connect(self):
        """建立HTTP连接"""
        if not self.session:
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=300,
                use_dns_cache=True
            )
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "CashUp/1.0.0"
                }
            )
            
            logger.info("Gate.io REST客户端连接已建立")
    
    async def close(self):
        """关闭HTTP连接"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Gate.io REST客户端连接已关闭")
    
    def _generate_signature(self, method: str, url: str, query_string: str = "", payload: str = "") -> Dict[str, str]:
        """
        生成API签名
        
        Args:
            method: HTTP方法
            url: 请求URL路径
            query_string: 查询字符串
            payload: 请求体
            
        Returns:
            包含签名信息的请求头
        """
        timestamp = str(int(time.time()))
        
        # 构建签名字符串
        message = f"{method}\n{url}\n{query_string}\n{hashlib.sha512(payload.encode()).hexdigest()}\n{timestamp}"
        
        # 生成签名
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha512
        ).hexdigest()
        
        return {
            "KEY": self.api_key,
            "Timestamp": timestamp,
            "SIGN": signature
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        auth_required: bool = True
    ) -> Dict[str, Any]:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            params: 查询参数
            data: 请求体数据
            auth_required: 是否需要认证
            
        Returns:
            API响应数据
        """
        if not self.session:
            await self.connect()
        
        url = f"{self.base_url}{endpoint}"
        
        # 处理查询参数
        query_string = ""
        if params:
            query_string = urlencode(sorted(params.items()))
            url = f"{url}?{query_string}"
        
        # 处理请求体
        payload = ""
        if data:
            payload = json.dumps(data, separators=(',', ':'))
        
        headers = {}
        
        # 添加认证头
        if auth_required:
            auth_headers = self._generate_signature(
                method.upper(),
                endpoint,
                query_string,
                payload
            )
            headers.update(auth_headers)
        
        try:
            async with self.session.request(
                method,
                url,
                headers=headers,
                data=payload if payload else None
            ) as response:
                
                response_text = await response.text()
                
                if response.status == 200:
                    return json.loads(response_text) if response_text else {}
                else:
                    logger.error(
                        f"Gate.io API请求失败: {response.status} {response_text}",
                        extra={
                            "method": method,
                            "endpoint": endpoint,
                            "status_code": response.status
                        }
                    )
                    raise Exception(f"API请求失败: {response.status} {response_text}")
                    
        except Exception as e:
            logger.error(
                f"Gate.io API请求异常: {e}",
                extra={
                    "method": method,
                    "endpoint": endpoint,
                    "error": str(e)
                }
            )
            raise
    
    # ==================== 现货交易API ====================
    
    async def get_spot_currencies(self) -> List[Dict]:
        """获取现货支持的币种列表"""
        return await self._request("GET", "/spot/currencies", auth_required=False)
    
    async def get_spot_currency_pairs(self) -> List[Dict]:
        """获取现货交易对列表"""
        return await self._request("GET", "/spot/currency_pairs", auth_required=False)
    
    async def get_spot_ticker(self, currency_pair: str) -> Dict:
        """获取现货交易对行情"""
        return await self._request(
            "GET",
            f"/spot/tickers",
            params={"currency_pair": currency_pair},
            auth_required=False
        )
    
    async def get_spot_order_book(self, currency_pair: str, limit: int = 10) -> Dict:
        """获取现货订单簿"""
        return await self._request(
            "GET",
            "/spot/order_book",
            params={"currency_pair": currency_pair, "limit": limit},
            auth_required=False
        )
    
    async def get_spot_trades(self, currency_pair: str, limit: int = 100) -> List[Dict]:
        """获取现货成交记录"""
        return await self._request(
            "GET",
            "/spot/trades",
            params={"currency_pair": currency_pair, "limit": limit},
            auth_required=False
        )
    
    async def get_spot_candlesticks(
        self,
        currency_pair: str,
        interval: str = "1m",
        limit: int = 100,
        from_time: Optional[int] = None,
        to_time: Optional[int] = None
    ) -> List[List]:
        """获取现货K线数据"""
        params = {
            "currency_pair": currency_pair,
            "interval": interval,
            "limit": limit
        }
        
        if from_time:
            params["from"] = from_time
        if to_time:
            params["to"] = to_time
        
        return await self._request(
            "GET",
            "/spot/candlesticks",
            params=params,
            auth_required=False
        )
    
    async def get_spot_accounts(self) -> List[Dict]:
        """获取现货账户余额"""
        return await self._request("GET", "/spot/accounts")
    
    async def create_spot_order(
        self,
        currency_pair: str,
        side: str,
        amount: str,
        price: Optional[str] = None,
        type_: str = "limit",
        account: str = "spot",
        time_in_force: str = "gtc",
        iceberg: Optional[str] = None,
        auto_borrow: bool = False,
        auto_repay: bool = False,
        text: Optional[str] = None
    ) -> Dict:
        """创建现货订单"""
        data = {
            "currency_pair": currency_pair,
            "side": side,
            "amount": amount,
            "type": type_,
            "account": account,
            "time_in_force": time_in_force,
            "auto_borrow": auto_borrow,
            "auto_repay": auto_repay
        }
        
        if price:
            data["price"] = price
        if iceberg:
            data["iceberg"] = iceberg
        if text:
            data["text"] = text
        
        return await self._request("POST", "/spot/orders", data=data)
    
    async def get_spot_orders(
        self,
        currency_pair: str,
        status: str = "open",
        page: int = 1,
        limit: int = 100
    ) -> List[Dict]:
        """获取现货订单列表"""
        return await self._request(
            "GET",
            "/spot/orders",
            params={
                "currency_pair": currency_pair,
                "status": status,
                "page": page,
                "limit": limit
            }
        )
    
    async def cancel_spot_orders(self, currency_pair: str, side: Optional[str] = None) -> List[Dict]:
        """批量取消现货订单"""
        params = {"currency_pair": currency_pair}
        if side:
            params["side"] = side
        
        return await self._request("DELETE", "/spot/orders", params=params)
    
    async def get_spot_order(self, order_id: str, currency_pair: str) -> Dict:
        """获取单个现货订单详情"""
        return await self._request(
            "GET",
            f"/spot/orders/{order_id}",
            params={"currency_pair": currency_pair}
        )
    
    async def cancel_spot_order(self, order_id: str, currency_pair: str) -> Dict:
        """取消单个现货订单"""
        return await self._request(
            "DELETE",
            f"/spot/orders/{order_id}",
            params={"currency_pair": currency_pair}
        )
    
    # ==================== 期货交易API ====================
    
    async def get_futures_contracts(self, settle: str = "usdt") -> List[Dict]:
        """获取期货合约列表"""
        return await self._request(
            "GET",
            f"/futures/{settle}/contracts",
            auth_required=False
        )
    
    async def get_futures_order_book(self, settle: str, contract: str, interval: str = "0", limit: int = 10) -> Dict:
        """获取期货订单簿"""
        return await self._request(
            "GET",
            f"/futures/{settle}/order_book",
            params={"contract": contract, "interval": interval, "limit": limit},
            auth_required=False
        )
    
    async def get_futures_tickers(self, settle: str, contract: Optional[str] = None) -> List[Dict]:
        """获取期货行情"""
        params = {}
        if contract:
            params["contract"] = contract
        
        return await self._request(
            "GET",
            f"/futures/{settle}/tickers",
            params=params,
            auth_required=False
        )
    
    async def get_futures_trades(self, settle: str, contract: str, limit: int = 100) -> List[Dict]:
        """获取期货成交记录"""
        return await self._request(
            "GET",
            f"/futures/{settle}/trades",
            params={"contract": contract, "limit": limit},
            auth_required=False
        )
    
    async def get_futures_candlesticks(
        self,
        settle: str,
        contract: str,
        interval: str = "1m",
        limit: int = 100,
        from_time: Optional[int] = None,
        to_time: Optional[int] = None
    ) -> List[List]:
        """获取期货K线数据"""
        params = {
            "contract": contract,
            "interval": interval,
            "limit": limit
        }
        
        if from_time:
            params["from"] = from_time
        if to_time:
            params["to"] = to_time
        
        return await self._request(
            "GET",
            f"/futures/{settle}/candlesticks",
            params=params,
            auth_required=False
        )
    
    async def get_futures_accounts(self, settle: str = "usdt") -> Dict:
        """获取期货账户信息"""
        return await self._request("GET", f"/futures/{settle}/accounts")
    
    async def get_futures_positions(self, settle: str = "usdt") -> List[Dict]:
        """获取期货持仓"""
        return await self._request("GET", f"/futures/{settle}/positions")
    
    async def create_futures_order(
        self,
        settle: str,
        contract: str,
        size: int,
        price: Optional[str] = None,
        tif: str = "gtc",
        text: Optional[str] = None,
        iceberg: Optional[int] = None,
        auto_size: Optional[str] = None,
        reduce_only: bool = False,
        close: bool = False
    ) -> Dict:
        """创建期货订单"""
        data = {
            "contract": contract,
            "size": size,
            "tif": tif,
            "reduce_only": reduce_only,
            "close": close
        }
        
        if price:
            data["price"] = price
        if text:
            data["text"] = text
        if iceberg:
            data["iceberg"] = iceberg
        if auto_size:
            data["auto_size"] = auto_size
        
        return await self._request("POST", f"/futures/{settle}/orders", data=data)
    
    async def get_futures_orders(
        self,
        settle: str,
        contract: str,
        status: str = "open",
        limit: int = 100
    ) -> List[Dict]:
        """获取期货订单列表"""
        return await self._request(
            "GET",
            f"/futures/{settle}/orders",
            params={
                "contract": contract,
                "status": status,
                "limit": limit
            }
        )
    
    async def cancel_futures_orders(self, settle: str, contract: str, side: Optional[str] = None) -> List[Dict]:
        """批量取消期货订单"""
        params = {"contract": contract}
        if side:
            params["side"] = side
        
        return await self._request("DELETE", f"/futures/{settle}/orders", params=params)
    
    async def get_futures_order(self, settle: str, order_id: str) -> Dict:
        """获取单个期货订单详情"""
        return await self._request("GET", f"/futures/{settle}/orders/{order_id}")
    
    async def cancel_futures_order(self, settle: str, order_id: str) -> Dict:
        """取消单个期货订单"""
        return await self._request("DELETE", f"/futures/{settle}/orders/{order_id}")


class GateIOWebSocketClient:
    """
    Gate.io WebSocket API客户端
    
    支持现货、期货的实时数据推送
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        testnet: bool = False
    ):
        """
        初始化Gate.io WebSocket客户端
        
        Args:
            api_key: API密钥（私有频道需要）
            api_secret: API密钥（私有频道需要）
            testnet: 是否使用测试网
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # WebSocket URL
        if testnet:
            self.spot_url = "wss://ws-testnet.gate.com/v4/ws"
            self.futures_url = "wss://fx-ws-testnet.gateio.ws/v4/ws/usdt"
        else:
            self.spot_url = "wss://api.gateio.ws/ws/v4/"
            self.futures_url = "wss://fx-ws.gateio.ws/v4/ws/usdt"
        
        # 连接状态
        self.spot_ws: Optional[websockets.WebSocketServerProtocol] = None
        self.futures_ws: Optional[websockets.WebSocketServerProtocol] = None
        
        # 订阅管理
        self.spot_subscriptions: Dict[str, Callable] = {}
        self.futures_subscriptions: Dict[str, Callable] = {}
        
        # 运行状态
        self.spot_running = False
        self.futures_running = False
    
    def _generate_auth(self, channel: str, event: str) -> Dict[str, str]:
        """
        生成WebSocket认证信息
        
        Args:
            channel: 频道名称
            event: 事件类型
            
        Returns:
            认证信息
        """
        if not self.api_key or not self.api_secret:
            raise ValueError("私有频道需要提供API密钥")
        
        timestamp = int(time.time())
        message = f"channel={channel}&event={event}&time={timestamp}"
        
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha512
        ).hexdigest()
        
        return {
            "method": "api_key",
            "KEY": self.api_key,
            "SIGN": signature
        }
    
    async def _handle_spot_message(self, message: str):
        """处理现货WebSocket消息"""
        try:
            data = json.loads(message)
            channel = data.get("channel")
            
            if channel in self.spot_subscriptions:
                callback = self.spot_subscriptions[channel]
                await callback(data)
            else:
                logger.debug(f"收到未订阅的现货频道消息: {channel}")
                
        except Exception as e:
            logger.error(f"处理现货WebSocket消息异常: {e}")
    
    async def _handle_futures_message(self, message: str):
        """处理期货WebSocket消息"""
        try:
            data = json.loads(message)
            channel = data.get("channel")
            
            if channel in self.futures_subscriptions:
                callback = self.futures_subscriptions[channel]
                await callback(data)
            else:
                logger.debug(f"收到未订阅的期货频道消息: {channel}")
                
        except Exception as e:
            logger.error(f"处理期货WebSocket消息异常: {e}")
    
    async def _spot_listener(self):
        """现货WebSocket监听器"""
        while self.spot_running:
            try:
                if not self.spot_ws:
                    self.spot_ws = await websockets.connect(self.spot_url)
                    logger.info("现货WebSocket连接已建立")
                
                async for message in self.spot_ws:
                    await self._handle_spot_message(message)
                    
            except ConnectionClosed:
                logger.warning("现货WebSocket连接已关闭，尝试重连...")
                self.spot_ws = None
                await asyncio.sleep(5)
                
            except WebSocketException as e:
                logger.error(f"现货WebSocket异常: {e}")
                self.spot_ws = None
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"现货WebSocket监听器异常: {e}")
                await asyncio.sleep(5)
    
    async def _futures_listener(self):
        """期货WebSocket监听器"""
        while self.futures_running:
            try:
                if not self.futures_ws:
                    self.futures_ws = await websockets.connect(self.futures_url)
                    logger.info("期货WebSocket连接已建立")
                
                async for message in self.futures_ws:
                    await self._handle_futures_message(message)
                    
            except ConnectionClosed:
                logger.warning("期货WebSocket连接已关闭，尝试重连...")
                self.futures_ws = None
                await asyncio.sleep(5)
                
            except WebSocketException as e:
                logger.error(f"期货WebSocket异常: {e}")
                self.futures_ws = None
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"期货WebSocket监听器异常: {e}")
                await asyncio.sleep(5)
    
    async def start_spot(self):
        """启动现货WebSocket连接"""
        if not self.spot_running:
            self.spot_running = True
            asyncio.create_task(self._spot_listener())
            logger.info("现货WebSocket客户端已启动")
    
    async def start_futures(self):
        """启动期货WebSocket连接"""
        if not self.futures_running:
            self.futures_running = True
            asyncio.create_task(self._futures_listener())
            logger.info("期货WebSocket客户端已启动")
    
    async def stop_spot(self):
        """停止现货WebSocket连接"""
        self.spot_running = False
        if self.spot_ws:
            await self.spot_ws.close()
            self.spot_ws = None
        logger.info("现货WebSocket客户端已停止")
    
    async def stop_futures(self):
        """停止期货WebSocket连接"""
        self.futures_running = False
        if self.futures_ws:
            await self.futures_ws.close()
            self.futures_ws = None
        logger.info("期货WebSocket客户端已停止")
    
    async def subscribe_spot_ticker(self, currency_pair: str, callback: Callable):
        """订阅现货行情"""
        channel = "spot.tickers"
        self.spot_subscriptions[channel] = callback
        
        if self.spot_ws:
            message = {
                "time": int(time.time()),
                "channel": channel,
                "event": "subscribe",
                "payload": [currency_pair]
            }
            await self.spot_ws.send(json.dumps(message))
            logger.info(f"已订阅现货行情: {currency_pair}")
    
    async def subscribe_spot_trades(self, currency_pair: str, callback: Callable):
        """订阅现货成交记录"""
        channel = "spot.trades"
        self.spot_subscriptions[channel] = callback
        
        if self.spot_ws:
            message = {
                "time": int(time.time()),
                "channel": channel,
                "event": "subscribe",
                "payload": [currency_pair]
            }
            await self.spot_ws.send(json.dumps(message))
            logger.info(f"已订阅现货成交记录: {currency_pair}")
    
    async def subscribe_spot_order_book(self, currency_pair: str, interval: str, limit: int, callback: Callable):
        """订阅现货订单簿"""
        channel = "spot.order_book_update"
        self.spot_subscriptions[channel] = callback
        
        if self.spot_ws:
            message = {
                "time": int(time.time()),
                "channel": channel,
                "event": "subscribe",
                "payload": [currency_pair, interval, str(limit)]
            }
            await self.spot_ws.send(json.dumps(message))
            logger.info(f"已订阅现货订单簿: {currency_pair}")
    
    async def subscribe_futures_ticker(self, contract: str, callback: Callable):
        """订阅期货行情"""
        channel = "futures.tickers"
        self.futures_subscriptions[channel] = callback
        
        if self.futures_ws:
            message = {
                "time": int(time.time()),
                "channel": channel,
                "event": "subscribe",
                "payload": [contract]
            }
            await self.futures_ws.send(json.dumps(message))
            logger.info(f"已订阅期货行情: {contract}")
    
    async def subscribe_futures_trades(self, contract: str, callback: Callable):
        """订阅期货成交记录"""
        channel = "futures.trades"
        self.futures_subscriptions[channel] = callback
        
        if self.futures_ws:
            message = {
                "time": int(time.time()),
                "channel": channel,
                "event": "subscribe",
                "payload": [contract]
            }
            await self.futures_ws.send(json.dumps(message))
            logger.info(f"已订阅期货成交记录: {contract}")
    
    async def subscribe_futures_order_book(self, contract: str, interval: str, limit: int, callback: Callable):
        """订阅期货订单簿"""
        channel = "futures.order_book_update"
        self.futures_subscriptions[channel] = callback
        
        if self.futures_ws:
            message = {
                "time": int(time.time()),
                "channel": channel,
                "event": "subscribe",
                "payload": [contract, interval, str(limit)]
            }
            await self.futures_ws.send(json.dumps(message))
            logger.info(f"已订阅期货订单簿: {contract}")
    
    async def subscribe_spot_orders(self, currency_pairs: List[str], callback: Callable):
        """订阅现货订单更新（需要认证）"""
        channel = "spot.orders"
        self.spot_subscriptions[channel] = callback
        
        if self.spot_ws:
            message = {
                "time": int(time.time()),
                "channel": channel,
                "event": "subscribe",
                "payload": currency_pairs,
                "auth": self._generate_auth(channel, "subscribe")
            }
            await self.spot_ws.send(json.dumps(message))
            logger.info(f"已订阅现货订单更新: {currency_pairs}")
    
    async def subscribe_futures_orders(self, contracts: List[str], callback: Callable):
        """订阅期货订单更新（需要认证）"""
        channel = "futures.orders"
        self.futures_subscriptions[channel] = callback
        
        if self.futures_ws:
            message = {
                "time": int(time.time()),
                "channel": channel,
                "event": "subscribe",
                "payload": contracts,
                "auth": self._generate_auth(channel, "subscribe")
            }
            await self.futures_ws.send(json.dumps(message))
            logger.info(f"已订阅期货订单更新: {contracts}")


class GateIOClient:
    """
    Gate.io统一客户端
    
    整合REST API和WebSocket API功能
    """
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False,
        timeout: int = 30
    ):
        """
        初始化Gate.io统一客户端
        
        Args:
            api_key: API密钥
            api_secret: API密钥
            testnet: 是否使用测试网
            timeout: 请求超时时间
        """
        self.rest_client = GateIORestClient(api_key, api_secret, testnet, timeout)
        self.ws_client = GateIOWebSocketClient(api_key, api_secret, testnet)
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.rest_client.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
    
    async def close(self):
        """关闭所有连接"""
        await self.rest_client.close()
        await self.ws_client.stop_spot()
        await self.ws_client.stop_futures()
        logger.info("Gate.io客户端已关闭")
    
    @property
    def rest(self) -> GateIORestClient:
        """获取REST API客户端"""
        return self.rest_client
    
    @property
    def ws(self) -> GateIOWebSocketClient:
        """获取WebSocket API客户端"""
        return self.ws_client