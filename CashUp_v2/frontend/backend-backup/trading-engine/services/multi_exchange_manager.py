"""
多交易所并行支持模块
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from .config_driven_manager import ConfigDrivenExchangeManager
from ..exchanges.base import ExchangeAdapter, Ticker, Balance, Order, Trade, Kline

logger = logging.getLogger(__name__)

@dataclass
class ExchangeRequest:
    """交易所请求"""
    exchange_name: str
    method: str
    params: Dict[str, Any] = field(default_factory=dict)
    timeout: float = 30.0
    priority: int = 0  # 优先级，数字越小优先级越高

@dataclass
class ExchangeResponse:
    """交易所响应"""
    exchange_name: str
    method: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    response_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ParallelRequestResult:
    """并行请求结果"""
    successful_requests: List[ExchangeResponse] = field(default_factory=list)
    failed_requests: List[ExchangeResponse] = field(default_factory=list)
    total_time: float = 0.0
    success_rate: float = 0.0

class MultiExchangeManager:
    """多交易所并行管理器"""
    
    def __init__(self, config_manager: ConfigDrivenExchangeManager):
        self.config_manager = config_manager
        self.request_timeout = 30.0
        self.max_concurrent_requests = 10
        self.retry_count = 3
        self.retry_delay = 1.0
        self.executor = ThreadPoolExecutor(max_workers=self.max_concurrent_requests)
        
        # 性能统计
        self.request_stats: Dict[str, Dict[str, Any]] = {}
        
    async def execute_parallel_requests(self, requests: List[ExchangeRequest]) -> ParallelRequestResult:
        """并行执行多个交易所请求"""
        start_time = time.time()
        
        # 按优先级排序
        sorted_requests = sorted(requests, key=lambda x: x.priority)
        
        # 创建异步任务
        tasks = []
        for request in sorted_requests:
            task = asyncio.create_task(self._execute_request(request))
            tasks.append(task)
        
        # 等待所有任务完成
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        successful_requests = []
        failed_requests = []
        
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                failed_requests.append(ExchangeResponse(
                    exchange_name=sorted_requests[i].exchange_name,
                    method=sorted_requests[i].method,
                    success=False,
                    error=str(response)
                ))
            else:
                if response.success:
                    successful_requests.append(response)
                else:
                    failed_requests.append(response)
        
        total_time = time.time() - start_time
        success_rate = len(successful_requests) / len(requests) if requests else 0
        
        return ParallelRequestResult(
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_time=total_time,
            success_rate=success_rate
        )
    
    async def _execute_request(self, request: ExchangeRequest) -> ExchangeResponse:
        """执行单个交易所请求"""
        start_time = time.time()
        
        try:
            # 获取交易所适配器
            adapter = self.config_manager.get_exchange_adapter(request.exchange_name)
            if not adapter:
                return ExchangeResponse(
                    exchange_name=request.exchange_name,
                    method=request.method,
                    success=False,
                    error=f"交易所适配器不存在: {request.exchange_name}"
                )
            
            # 执行请求
            result = await asyncio.wait_for(
                self._call_exchange_method(adapter, request.method, request.params),
                timeout=request.timeout
            )
            
            response_time = time.time() - start_time
            
            # 更新统计信息
            self._update_stats(request.exchange_name, request.method, True, response_time)
            
            return ExchangeResponse(
                exchange_name=request.exchange_name,
                method=request.method,
                success=True,
                data=result,
                response_time=response_time
            )
            
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            self._update_stats(request.exchange_name, request.method, False, response_time)
            
            return ExchangeResponse(
                exchange_name=request.exchange_name,
                method=request.method,
                success=False,
                error="请求超时",
                response_time=response_time
            )
        except Exception as e:
            response_time = time.time() - start_time
            self._update_stats(request.exchange_name, request.method, False, response_time)
            
            return ExchangeResponse(
                exchange_name=request.exchange_name,
                method=request.method,
                success=False,
                error=str(e),
                response_time=response_time
            )
    
    async def _call_exchange_method(self, adapter: ExchangeAdapter, method: str, params: Dict[str, Any]) -> Any:
        """调用交易所方法"""
        # 根据方法名调用相应的适配器方法
        if method == "get_ticker":
            return await adapter.get_ticker(params.get("symbol"))
        elif method == "get_balance":
            return await adapter.get_balance()
        elif method == "get_orders":
            return await adapter.get_orders(
                params.get("symbol"),
                params.get("status")
            )
        elif method == "get_klines":
            return await adapter.get_klines(
                params.get("symbol"),
                params.get("interval"),
                params.get("start_time"),
                params.get("end_time"),
                params.get("limit", 100)
            )
        elif method == "place_order":
            return await adapter.place_order(params.get("order_request"))
        elif method == "cancel_order":
            return await adapter.cancel_order(params.get("cancel_request"))
        else:
            raise ValueError(f"不支持的方法: {method}")
    
    def _update_stats(self, exchange_name: str, method: str, success: bool, response_time: float):
        """更新统计信息"""
        key = f"{exchange_name}.{method}"
        
        if key not in self.request_stats:
            self.request_stats[key] = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_response_time": 0.0,
                "avg_response_time": 0.0,
                "success_rate": 0.0
            }
        
        stats = self.request_stats[key]
        stats["total_requests"] += 1
        
        if success:
            stats["successful_requests"] += 1
        else:
            stats["failed_requests"] += 1
        
        stats["total_response_time"] += response_time
        stats["avg_response_time"] = stats["total_response_time"] / stats["total_requests"]
        stats["success_rate"] = stats["successful_requests"] / stats["total_requests"]
    
    def get_request_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取请求统计信息"""
        return self.request_stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        self.request_stats.clear()

class MultiExchangeDataFetcher:
    """多交易所数据获取器"""
    
    def __init__(self, multi_exchange_manager: MultiExchangeManager):
        self.manager = multi_exchange_manager
        
    async def get_tickers_from_all_exchanges(self, symbol: str) -> Dict[str, Ticker]:
        """从所有交易所获取行情"""
        requests = []
        
        for exchange_name in self.manager.config_manager.get_enabled_exchange_names():
            requests.append(ExchangeRequest(
                exchange_name=exchange_name,
                method="get_ticker",
                params={"symbol": symbol}
            ))
        
        result = await self.manager.execute_parallel_requests(requests)
        
        tickers = {}
        for response in result.successful_requests:
            if response.data:
                tickers[response.exchange_name] = response.data
        
        return tickers
    
    async def get_balances_from_all_exchanges(self) -> Dict[str, Dict[str, Balance]]:
        """从所有交易所获取余额"""
        requests = []
        
        for exchange_name in self.manager.config_manager.get_enabled_exchange_names():
            requests.append(ExchangeRequest(
                exchange_name=exchange_name,
                method="get_balance"
            ))
        
        result = await self.manager.execute_parallel_requests(requests)
        
        balances = {}
        for response in result.successful_requests:
            if response.data:
                balances[response.exchange_name] = response.data
        
        return balances
    
    async def get_orders_from_all_exchanges(self, symbol: Optional[str] = None, 
                                           status=None) -> Dict[str, List[Order]]:
        """从所有交易所获取订单"""
        requests = []
        
        for exchange_name in self.manager.config_manager.get_enabled_exchange_names():
            requests.append(ExchangeRequest(
                exchange_name=exchange_name,
                method="get_orders",
                params={"symbol": symbol, "status": status}
            ))
        
        result = await self.manager.execute_parallel_requests(requests)
        
        orders = {}
        for response in result.successful_requests:
            if response.data:
                orders[response.exchange_name] = response.data
        
        return orders
    
    async def get_klines_from_all_exchanges(self, symbol: str, interval: str,
                                           start_time=None, end_time=None,
                                           limit: int = 100) -> Dict[str, List[Kline]]:
        """从所有交易所获取K线数据"""
        requests = []
        
        for exchange_name in self.manager.config_manager.get_enabled_exchange_names():
            requests.append(ExchangeRequest(
                exchange_name=exchange_name,
                method="get_klines",
                params={
                    "symbol": symbol,
                    "interval": interval,
                    "start_time": start_time,
                    "end_time": end_time,
                    "limit": limit
                }
            ))
        
        result = await self.manager.execute_parallel_requests(requests)
        
        klines = {}
        for response in result.successful_requests:
            if response.data:
                klines[response.exchange_name] = response.data
        
        return klines

class MultiExchangeOrderManager:
    """多交易所订单管理器"""
    
    def __init__(self, multi_exchange_manager: MultiExchangeManager):
        self.manager = multi_exchange_manager
        
    async def place_order_on_best_exchange(self, order_request, exchanges: Optional[List[str]] = None) -> Dict[str, Any]:
        """在最优交易所下单"""
        if not exchanges:
            exchanges = self.manager.config_manager.get_enabled_exchange_names()
        
        # 获取所有交易所的行情
        symbol = order_request.symbol
        tickers = await MultiExchangeDataFetcher(self.manager).get_tickers_from_all_exchanges(symbol)
        
        # 选择最优交易所（这里简单使用最低价格，实际可以根据策略选择）
        best_exchange = None
        best_price = None
        
        for exchange_name, ticker in tickers.items():
            if exchange_name in exchanges:
                if order_request.side.value == "buy":
                    price = ticker.ask_price
                else:
                    price = ticker.bid_price
                
                if best_price is None or (
                    order_request.side.value == "buy" and price < best_price
                ) or (
                    order_request.side.value == "sell" and price > best_price
                ):
                    best_price = price
                    best_exchange = exchange_name
        
        if not best_exchange:
            return {"success": False, "error": "没有可用的交易所"}
        
        # 在最优交易所下单
        request = ExchangeRequest(
            exchange_name=best_exchange,
            method="place_order",
            params={"order_request": order_request}
        )
        
        result = await self.manager.execute_parallel_requests([request])
        
        if result.successful_requests:
            return {
                "success": True,
                "exchange": best_exchange,
                "order": result.successful_requests[0].data,
                "price": best_price
            }
        else:
            return {
                "success": False,
                "error": result.failed_requests[0].error if result.failed_requests else "下单失败"
            }
    
    async def place_order_on_multiple_exchanges(self, order_request, 
                                              exchanges: Optional[List[str]] = None,
                                              amounts: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """在多个交易所同时下单"""
        if not exchanges:
            exchanges = self.manager.config_manager.get_enabled_exchange_names()
        
        requests = []
        
        for exchange_name in exchanges:
            # 为每个交易所创建订单请求
            exchange_order_request = order_request
            
            # 如果指定了金额分配，调整数量
            if amounts and exchange_name in amounts:
                # 创建订单请求的副本并调整数量
                # 这里需要根据实际订单类型来调整
                pass
            
            requests.append(ExchangeRequest(
                exchange_name=exchange_name,
                method="place_order",
                params={"order_request": exchange_order_request}
            ))
        
        result = await self.manager.execute_parallel_requests(requests)
        
        return {
            "success": len(result.successful_requests) > 0,
            "successful_orders": {
                response.exchange_name: response.data 
                for response in result.successful_requests
            },
            "failed_orders": {
                response.exchange_name: response.error 
                for response in result.failed_requests
            },
            "success_rate": result.success_rate
        }
    
    async def cancel_orders_on_all_exchanges(self, symbol: str) -> Dict[str, Any]:
        """取消所有交易所的指定交易对订单"""
        requests = []
        
        for exchange_name in self.manager.config_manager.get_enabled_exchange_names():
            # 获取该交易所的订单
            adapter = self.manager.config_manager.get_exchange_adapter(exchange_name)
            if adapter:
                orders = await adapter.get_orders(symbol)
                
                # 为每个订单创建取消请求
                for order in orders:
                    requests.append(ExchangeRequest(
                        exchange_name=exchange_name,
                        method="cancel_order",
                        params={
                            "cancel_request": {
                                "symbol": symbol,
                                "order_id": order.id
                            }
                        }
                    ))
        
        result = await self.manager.execute_parallel_requests(requests)
        
        return {
            "success": len(result.successful_requests) > 0,
            "cancelled_count": len(result.successful_requests),
            "failed_count": len(result.failed_requests),
            "success_rate": result.success_rate
        }

class MultiExchangeArbitrage:
    """多交易所套利模块"""
    
    def __init__(self, multi_exchange_manager: MultiExchangeManager):
        self.manager = multi_exchange_manager
        self.data_fetcher = MultiExchangeDataFetcher(multi_exchange_manager)
        self.order_manager = MultiExchangeOrderManager(multi_exchange_manager)
        
    async def find_arbitrage_opportunities(self, symbol: str, min_profit_threshold: float = 0.001) -> List[Dict[str, Any]]:
        """寻找套利机会"""
        # 获取所有交易所的行情
        tickers = await self.data_fetcher.get_tickers_from_all_exchanges(symbol)
        
        opportunities = []
        exchanges = list(tickers.keys())
        
        # 比较所有交易所对
        for i in range(len(exchanges)):
            for j in range(i + 1, len(exchanges)):
                exchange1 = exchanges[i]
                exchange2 = exchanges[j]
                
                ticker1 = tickers[exchange1]
                ticker2 = tickers[exchange2]
                
                # 计算价差
                buy_price = ticker1.ask_price
                sell_price = ticker2.bid_price
                
                if buy_price > 0 and sell_price > 0:
                    profit_rate = (sell_price - buy_price) / buy_price
                    
                    if profit_rate > min_profit_threshold:
                        opportunities.append({
                            "buy_exchange": exchange1,
                            "sell_exchange": exchange2,
                            "buy_price": buy_price,
                            "sell_price": sell_price,
                            "profit_rate": profit_rate,
                            "symbol": symbol
                        })
        
        # 按利润率排序
        opportunities.sort(key=lambda x: x["profit_rate"], reverse=True)
        
        return opportunities
    
    async def execute_arbitrage(self, opportunity: Dict[str, Any], amount: float) -> Dict[str, Any]:
        """执行套利交易"""
        buy_exchange = opportunity["buy_exchange"]
        sell_exchange = opportunity["sell_exchange"]
        symbol = opportunity["symbol"]
        
        # 创建买入和卖出订单
        from ..exchanges.base import OrderRequest, OrderSide
        
        buy_order = OrderRequest(
            symbol=symbol,
            side=OrderSide.BUY,
            type=opportunity.get("buy_type", "market"),
            quantity=amount
        )
        
        sell_order = OrderRequest(
            symbol=symbol,
            side=OrderSide.SELL,
            type=opportunity.get("sell_type", "market"),
            quantity=amount
        )
        
        # 并行执行订单
        requests = [
            ExchangeRequest(
                exchange_name=buy_exchange,
                method="place_order",
                params={"order_request": buy_order}
            ),
            ExchangeRequest(
                exchange_name=sell_exchange,
                method="place_order",
                params={"order_request": sell_order}
            )
        ]
        
        result = await self.manager.execute_parallel_requests(requests)
        
        return {
            "success": len(result.successful_requests) == 2,
            "buy_result": result.successful_requests[0].data if len(result.successful_requests) > 0 else None,
            "sell_result": result.successful_requests[1].data if len(result.successful_requests) > 1 else None,
            "errors": [response.error for response in result.failed_requests]
        }