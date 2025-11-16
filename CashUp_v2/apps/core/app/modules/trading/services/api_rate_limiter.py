"""
API限流和错误处理模块
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import json
import traceback

from ..exchanges.base import ExchangeBase, ExchangeAdapter

logger = logging.getLogger(__name__)

class RateLimitType(Enum):
    """限流类型"""
    REQUESTS_PER_SECOND = "requests_per_second"
    REQUESTS_PER_MINUTE = "requests_per_minute"
    REQUESTS_PER_HOUR = "requests_per_hour"
    REQUESTS_PER_DAY = "requests_per_day"

class ErrorType(Enum):
    """错误类型"""
    NETWORK_ERROR = "network_error"
    API_ERROR = "api_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    AUTHENTICATION_ERROR = "authentication_error"
    VALIDATION_ERROR = "validation_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"

class RetryStrategy(Enum):
    """重试策略"""
    IMMEDIATE = "immediate"
    LINEAR_BACKOFF = "linear_backoff"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_DELAY = "fixed_delay"

@dataclass
class RateLimitConfig:
    """限流配置"""
    limit_type: RateLimitType
    limit: int
    window_size: int  # 窗口大小（秒）
    
@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    base_delay: float = 1.0
    max_delay: float = 60.0
    retryable_errors: List[ErrorType] = field(default_factory=lambda: [
        ErrorType.NETWORK_ERROR,
        ErrorType.API_ERROR,
        ErrorType.RATE_LIMIT_ERROR,
        ErrorType.TIMEOUT_ERROR
    ])

@dataclass
class APIRequest:
    """API请求"""
    exchange_name: str
    method: str
    endpoint: str
    params: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    request_id: str = field(default_factory=str)

@dataclass
class APIResponse:
    """API响应"""
    request: APIRequest
    success: bool
    data: Any = None
    error: Optional[str] = None
    error_type: Optional[ErrorType] = None
    response_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0

class RateLimiter:
    """令牌桶限流器"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.tokens = config.limit
        self.last_refill = time.time()
        self.lock = asyncio.Lock()
        
    async def acquire(self, tokens: int = 1) -> bool:
        """获取令牌"""
        async with self.lock:
            # 重新填充令牌
            self._refill_tokens()
            
            # 检查是否有足够的令牌
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    def _refill_tokens(self):
        """重新填充令牌"""
        now = time.time()
        time_passed = now - self.last_refill
        
        # 计算应该添加的令牌数
        tokens_to_add = (time_passed / self.config.window_size) * self.config.limit
        
        # 更新令牌数
        self.tokens = min(self.config.limit, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def get_status(self) -> Dict[str, Any]:
        """获取限流器状态"""
        self._refill_tokens()
        return {
            "limit": self.config.limit,
            "available_tokens": self.tokens,
            "usage_rate": (self.config.limit - self.tokens) / self.config.limit,
            "window_size": self.config.window_size,
            "limit_type": self.config.limit_type.value
        }

class SlidingWindowRateLimiter:
    """滑动窗口限流器"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.requests = deque()
        self.lock = asyncio.Lock()
        
    async def allow_request(self) -> bool:
        """检查是否允许请求"""
        async with self.lock:
            now = time.time()
            window_start = now - self.config.window_size
            
            # 清理窗口外的请求
            while self.requests and self.requests[0] < window_start:
                self.requests.popleft()
            
            # 检查是否超过限制
            if len(self.requests) < self.config.limit:
                self.requests.append(now)
                return True
            
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取限流器状态"""
        now = time.time()
        window_start = now - self.config.window_size
        
        # 清理窗口外的请求
        while self.requests and self.requests[0] < window_start:
            self.requests.popleft()
        
        return {
            "limit": self.config.limit,
            "current_requests": len(self.requests),
            "usage_rate": len(self.requests) / self.config.limit,
            "window_size": self.config.window_size,
            "limit_type": self.config.limit_type.value
        }

class ErrorHandler:
    """错误处理器"""
    
    def __init__(self, retry_config: RetryConfig):
        self.retry_config = retry_config
        self.error_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_errors": 0,
            "error_types": defaultdict(int),
            "last_error": None,
            "retry_count": 0
        })
        
    def classify_error(self, error: Exception) -> ErrorType:
        """分类错误"""
        error_str = str(error).lower()
        
        if isinstance(error, (ConnectionError, OSError)):
            return ErrorType.NETWORK_ERROR
        elif "timeout" in error_str:
            return ErrorType.TIMEOUT_ERROR
        elif "rate limit" in error_str or "too many requests" in error_str:
            return ErrorType.RATE_LIMIT_ERROR
        elif "unauthorized" in error_str or "authentication" in error_str:
            return ErrorType.AUTHENTICATION_ERROR
        elif "validation" in error_str or "invalid" in error_str:
            return ErrorType.VALIDATION_ERROR
        elif "api" in error_str or "server" in error_str:
            return ErrorType.API_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR
    
    def should_retry(self, error: Exception, retry_count: int) -> bool:
        """判断是否应该重试"""
        if retry_count >= self.retry_config.max_retries:
            return False
        
        error_type = self.classify_error(error)
        return error_type in self.retry_config.retryable_errors
    
    def get_retry_delay(self, retry_count: int) -> float:
        """获取重试延迟"""
        if self.retry_config.retry_strategy == RetryStrategy.IMMEDIATE:
            return 0.0
        elif self.retry_config.retry_strategy == RetryStrategy.FIXED_DELAY:
            return self.retry_config.base_delay
        elif self.retry_config.retry_strategy == RetryStrategy.LINEAR_BACKOFF:
            return min(self.retry_config.base_delay * (retry_count + 1), self.retry_config.max_delay)
        elif self.retry_config.retry_strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            return min(self.retry_config.base_delay * (2 ** retry_count), self.retry_config.max_delay)
        else:
            return self.retry_config.base_delay
    
    def log_error(self, exchange_name: str, error: Exception, retry_count: int = 0):
        """记录错误"""
        error_type = self.classify_error(error)
        
        stats = self.error_stats[exchange_name]
        stats["total_errors"] += 1
        stats["error_types"][error_type.value] += 1
        stats["last_error"] = {
            "type": error_type.value,
            "message": str(error),
            "timestamp": datetime.now().isoformat()
        }
        stats["retry_count"] += retry_count
        
        logger.warning(f"交易所 {exchange_name} 错误: {error_type.value} - {str(error)}")
    
    def get_error_stats(self, exchange_name: Optional[str] = None) -> Dict[str, Any]:
        """获取错误统计"""
        if exchange_name:
            return dict(self.error_stats[exchange_name])
        else:
            return {name: dict(stats) for name, stats in self.error_stats.items()}
    
    def reset_stats(self, exchange_name: Optional[str] = None):
        """重置错误统计"""
        if exchange_name:
            if exchange_name in self.error_stats:
                del self.error_stats[exchange_name]
        else:
            self.error_stats.clear()

class APIRequestHandler:
    """API请求处理器"""
    
    def __init__(self, rate_limit_configs: List[RateLimitConfig], retry_config: RetryConfig):
        self.rate_limiters: Dict[str, List[RateLimiter]] = {}
        self.sliding_window_limiters: Dict[str, List[SlidingWindowRateLimiter]] = {}
        self.error_handler = ErrorHandler(retry_config)
        
        # 初始化限流器
        for config in rate_limit_configs:
            # 为每个交易所创建限流器
            if config.limit_type in [RateLimitType.REQUESTS_PER_SECOND]:
                limiter = RateLimiter(config)
                if "default" not in self.rate_limiters:
                    self.rate_limiters["default"] = []
                self.rate_limiters["default"].append(limiter)
            else:
                limiter = SlidingWindowRateLimiter(config)
                if "default" not in self.sliding_window_limiters:
                    self.sliding_window_limiters["default"] = []
                self.sliding_window_limiters["default"].append(limiter)
    
    async def execute_request(self, request_func: Callable, exchange_name: str, 
                            *args, **kwargs) -> APIResponse:
        """执行API请求"""
        request_id = f"{exchange_name}_{int(time.time() * 1000)}"
        request = APIRequest(
            exchange_name=exchange_name,
            method=request_func.__name__,
            endpoint=kwargs.get("endpoint", "unknown"),
            params=kwargs,
            request_id=request_id
        )
        
        retry_count = 0
        last_error = None
        
        while retry_count <= self.error_handler.retry_config.max_retries:
            try:
                # 检查限流
                await self._check_rate_limits(exchange_name)
                
                # 执行请求
                start_time = time.time()
                result = await request_func(*args, **kwargs)
                response_time = time.time() - start_time
                
                return APIResponse(
                    request=request,
                    success=True,
                    data=result,
                    response_time=response_time,
                    retry_count=retry_count
                )
                
            except Exception as e:
                last_error = e
                retry_count += 1
                
                # 记录错误
                self.error_handler.log_error(exchange_name, e, retry_count)
                
                # 检查是否应该重试
                if not self.error_handler.should_retry(e, retry_count):
                    break
                
                # 获取重试延迟
                delay = self.error_handler.get_retry_delay(retry_count - 1)
                
                if delay > 0:
                    logger.info(f"交易所 {exchange_name} 请求失败，{delay:.2f}s后重试 (第{retry_count}次): {str(e)}")
                    await asyncio.sleep(delay)
        
        # 所有重试都失败了
        error_type = self.error_handler.classify_error(last_error) if last_error else ErrorType.UNKNOWN_ERROR
        
        return APIResponse(
            request=request,
            success=False,
            error=str(last_error) if last_error else "Unknown error",
            error_type=error_type,
            retry_count=retry_count - 1
        )
    
    async def _check_rate_limits(self, exchange_name: str):
        """检查限流"""
        # 检查令牌桶限流
        limiters = self.rate_limiters.get(exchange_name, self.rate_limiters.get("default", []))
        for limiter in limiters:
            if not await limiter.acquire():
                # 如果没有令牌，等待一段时间
                await asyncio.sleep(0.1)
                if not await limiter.acquire():
                    raise Exception(f"Rate limit exceeded for {exchange_name}")
        
        # 检查滑动窗口限流
        window_limiters = self.sliding_window_limiters.get(exchange_name, self.sliding_window_limiters.get("default", []))
        for limiter in window_limiters:
            if not await limiter.allow_request():
                raise Exception(f"Sliding window rate limit exceeded for {exchange_name}")
    
    def get_rate_limit_status(self, exchange_name: str) -> Dict[str, Any]:
        """获取限流状态"""
        status = {}
        
        # 获取令牌桶限流器状态
        limiters = self.rate_limiters.get(exchange_name, self.rate_limiters.get("default", []))
        for i, limiter in enumerate(limiters):
            status[f"token_bucket_{i}"] = limiter.get_status()
        
        # 获取滑动窗口限流器状态
        window_limiters = self.sliding_window_limiters.get(exchange_name, self.sliding_window_limiters.get("default", []))
        for i, limiter in enumerate(window_limiters):
            status[f"sliding_window_{i}"] = limiter.get_status()
        
        return status
    
    def get_error_stats(self, exchange_name: Optional[str] = None) -> Dict[str, Any]:
        """获取错误统计"""
        return self.error_handler.get_error_stats(exchange_name)

class ExchangeAPIWrapper:
    """交易所API包装器"""
    
    def __init__(self, exchange_adapter: ExchangeAdapter, 
                 rate_limit_configs: List[RateLimitConfig],
                 retry_config: RetryConfig):
        self.exchange_adapter = exchange_adapter
        self.exchange_name = exchange_adapter.name
        self.request_handler = APIRequestHandler(rate_limit_configs, retry_config)
        
        # 性能统计
        self.request_stats: Dict[str, Any] = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0.0,
            "avg_response_time": 0.0,
            "success_rate": 0.0
        }
        
    async def get_ticker(self, symbol: str) -> APIResponse:
        """获取行情"""
        response = await self.request_handler.execute_request(
            self.exchange_adapter.get_ticker,
            self.exchange_name,
            symbol
        )
        self._update_stats(response)
        return response
    
    async def get_balance(self) -> APIResponse:
        """获取余额"""
        response = await self.request_handler.execute_request(
            self.exchange_adapter.get_balance,
            self.exchange_name
        )
        self._update_stats(response)
        return response
    
    async def get_orders(self, symbol: Optional[str] = None, 
                        status=None) -> APIResponse:
        """获取订单"""
        response = await self.request_handler.execute_request(
            self.exchange_adapter.get_orders,
            self.exchange_name,
            symbol,
            status
        )
        self._update_stats(response)
        return response
    
    async def place_order(self, order_request) -> APIResponse:
        """下单"""
        response = await self.request_handler.execute_request(
            self.exchange_adapter.place_order,
            self.exchange_name,
            order_request
        )
        self._update_stats(response)
        return response
    
    async def cancel_order(self, cancel_request) -> APIResponse:
        """取消订单"""
        response = await self.request_handler.execute_request(
            self.exchange_adapter.cancel_order,
            self.exchange_name,
            cancel_request
        )
        self._update_stats(response)
        return response
    
    async def get_klines(self, symbol: str, interval: str,
                        start_time=None, end_time=None,
                        limit: int = 100) -> APIResponse:
        """获取K线数据"""
        response = await self.request_handler.execute_request(
            self.exchange_adapter.get_klines,
            self.exchange_name,
            symbol,
            interval,
            start_time,
            end_time,
            limit
        )
        self._update_stats(response)
        return response
    
    def _update_stats(self, response: APIResponse):
        """更新统计信息"""
        stats = self.request_stats
        stats["total_requests"] += 1
        
        if response.success:
            stats["successful_requests"] += 1
        else:
            stats["failed_requests"] += 1
        
        stats["total_response_time"] += response.response_time
        stats["avg_response_time"] = stats["total_response_time"] / stats["total_requests"]
        stats["success_rate"] = stats["successful_requests"] / stats["total_requests"]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "exchange_name": self.exchange_name,
            **self.request_stats,
            "rate_limit_status": self.request_handler.get_rate_limit_status(self.exchange_name),
            "error_stats": self.request_handler.get_error_stats(self.exchange_name)
        }

class ExchangeAPIManager:
    """交易所API管理器"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.wrappers: Dict[str, ExchangeAPIWrapper] = {}
        
        # 默认配置
        self.rate_limit_configs = [
            RateLimitConfig(RateLimitType.REQUESTS_PER_SECOND, 10, 1),
            RateLimitConfig(RateLimitType.REQUESTS_PER_MINUTE, 600, 60),
            RateLimitConfig(RateLimitType.REQUESTS_PER_HOUR, 36000, 3600)
        ]
        
        self.retry_config = RetryConfig(
            max_retries=3,
            retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=1.0,
            max_delay=60.0
        )
        
        self._initialize_wrappers()
    
    def _initialize_wrappers(self):
        """初始化API包装器"""
        for exchange_name, adapter in self.config_manager.exchange_adapters.items():
            wrapper = ExchangeAPIWrapper(
                adapter,
                self.rate_limit_configs,
                self.retry_config
            )
            self.wrappers[exchange_name] = wrapper
    
    def get_wrapper(self, exchange_name: str) -> Optional[ExchangeAPIWrapper]:
        """获取API包装器"""
        return self.wrappers.get(exchange_name)
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有统计信息"""
        return {
            exchange_name: wrapper.get_stats()
            for exchange_name, wrapper in self.wrappers.items()
        }
    
    def update_rate_limit_config(self, exchange_name: str, configs: List[RateLimitConfig]):
        """更新限流配置"""
        wrapper = self.wrappers.get(exchange_name)
        if wrapper:
            wrapper.request_handler.rate_limit_configs = configs
            logger.info(f"已更新 {exchange_name} 的限流配置")
    
    def update_retry_config(self, exchange_name: str, config: RetryConfig):
        """更新重试配置"""
        wrapper = self.wrappers.get(exchange_name)
        if wrapper:
            wrapper.request_handler.error_handler.retry_config = config
            logger.info(f"已更新 {exchange_name} 的重试配置")

# 默认限流配置
DEFAULT_RATE_LIMIT_CONFIGS = [
    RateLimitConfig(RateLimitType.REQUESTS_PER_SECOND, 10, 1),
    RateLimitConfig(RateLimitType.REQUESTS_PER_MINUTE, 600, 60),
    RateLimitConfig(RateLimitType.REQUESTS_PER_HOUR, 36000, 3600)
]

# 默认重试配置
DEFAULT_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
    base_delay=1.0,
    max_delay=60.0
)