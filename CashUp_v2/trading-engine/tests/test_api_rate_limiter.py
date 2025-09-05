"""
API限流和错误处理测试
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
import time

from services.api_rate_limiter import (
    RateLimiter, SlidingWindowRateLimiter, ErrorHandler, APIRequestHandler,
    ExchangeAPIWrapper, ExchangeAPIManager,
    RateLimitConfig, RetryConfig, APIRequest, APIResponse,
    RateLimitType, ErrorType, RetryStrategy, DEFAULT_RATE_LIMIT_CONFIGS, DEFAULT_RETRY_CONFIG
)
from config.exchange_config import ExchangeConfigManager, ExchangeConfig
from exchanges.base import ExchangeAdapter

class TestRateLimiter:
    """限流器测试"""
    
    def test_token_bucket_rate_limiter(self):
        """测试令牌桶限流器"""
        config = RateLimitConfig(RateLimitType.REQUESTS_PER_SECOND, 5, 1)
        limiter = RateLimiter(config)
        
        # 初始状态
        status = limiter.get_status()
        assert status["available_tokens"] == 5
        assert status["usage_rate"] == 0.0
        
        # 获取令牌
        assert asyncio.run(limiter.acquire(1)) is True
        assert asyncio.run(limiter.acquire(2)) is True
        
        # 检查剩余令牌
        status = limiter.get_status()
        assert status["available_tokens"] == 2
        
        # 获取超过限制的令牌
        assert asyncio.run(limiter.acquire(3)) is True
        assert asyncio.run(limiter.acquire(1)) is False  # 应该失败
        
        # 等待令牌重新填充
        time.sleep(0.2)
        status = limiter.get_status()
        assert status["available_tokens"] > 0
    
    def test_sliding_window_rate_limiter(self):
        """测试滑动窗口限流器"""
        config = RateLimitConfig(RateLimitType.REQUESTS_PER_MINUTE, 3, 60)
        limiter = SlidingWindowRateLimiter(config)
        
        # 初始状态
        status = limiter.get_status()
        assert status["current_requests"] == 0
        assert status["usage_rate"] == 0.0
        
        # 允许请求
        assert asyncio.run(limiter.allow_request()) is True
        assert asyncio.run(limiter.allow_request()) is True
        assert asyncio.run(limiter.allow_request()) is True
        
        # 超过限制
        assert asyncio.run(limiter.allow_request()) is False
        
        # 检查状态
        status = limiter.get_status()
        assert status["current_requests"] == 3
        assert status["usage_rate"] == 1.0

class TestErrorHandler:
    """错误处理器测试"""
    
    def setup_method(self):
        """设置测试环境"""
        self.retry_config = RetryConfig(
            max_retries=3,
            retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=1.0,
            max_delay=60.0
        )
        self.error_handler = ErrorHandler(self.retry_config)
    
    def test_error_classification(self):
        """测试错误分类"""
        # 网络错误
        network_error = ConnectionError("Connection failed")
        assert self.error_handler.classify_error(network_error) == ErrorType.NETWORK_ERROR
        
        # 超时错误
        timeout_error = TimeoutError("Request timeout")
        assert self.error_handler.classify_error(timeout_error) == ErrorType.TIMEOUT_ERROR
        
        # 限流错误
        rate_limit_error = Exception("Rate limit exceeded")
        assert self.error_handler.classify_error(rate_limit_error) == ErrorType.RATE_LIMIT_ERROR
        
        # 认证错误
        auth_error = Exception("Unauthorized access")
        assert self.error_handler.classify_error(auth_error) == ErrorType.AUTHENTICATION_ERROR
        
        # 验证错误
        validation_error = Exception("Invalid parameter")
        assert self.error_handler.classify_error(validation_error) == ErrorType.VALIDATION_ERROR
        
        # API错误
        api_error = Exception("API server error")
        assert self.error_handler.classify_error(api_error) == ErrorType.API_ERROR
        
        # 未知错误
        unknown_error = Exception("Unknown error")
        assert self.error_handler.classify_error(unknown_error) == ErrorType.UNKNOWN_ERROR
    
    def test_should_retry(self):
        """测试重试判断"""
        # 可重试错误
        retryable_error = ConnectionError("Network failed")
        assert self.error_handler.should_retry(retryable_error, 0) is True
        assert self.error_handler.should_retry(retryable_error, 2) is True
        assert self.error_handler.should_retry(retryable_error, 3) is False  # 超过最大重试次数
        
        # 不可重试错误
        non_retryable_error = Exception("Unauthorized")
        assert self.error_handler.should_retry(non_retryable_error, 0) is False
    
    def test_retry_delay_calculation(self):
        """测试重试延迟计算"""
        # 立即重试
        self.retry_config.retry_strategy = RetryStrategy.IMMEDIATE
        assert self.error_handler.get_retry_delay(0) == 0.0
        assert self.error_handler.get_retry_delay(2) == 0.0
        
        # 固定延迟
        self.retry_config.retry_strategy = RetryStrategy.FIXED_DELAY
        assert self.error_handler.get_retry_delay(0) == 1.0
        assert self.error_handler.get_retry_delay(2) == 1.0
        
        # 线性退避
        self.retry_config.retry_strategy = RetryStrategy.LINEAR_BACKOFF
        assert self.error_handler.get_retry_delay(0) == 1.0
        assert self.error_handler.get_retry_delay(2) == 3.0
        
        # 指数退避
        self.retry_config.retry_strategy = RetryStrategy.EXPONENTIAL_BACKOFF
        assert self.error_handler.get_retry_delay(0) == 1.0
        assert self.error_handler.get_retry_delay(2) == 4.0
        
        # 最大延迟限制
        self.retry_config.base_delay = 10.0
        self.retry_config.max_delay = 15.0
        assert self.error_handler.get_retry_delay(3) == 15.0  # 应该被限制
    
    def test_error_logging(self):
        """测试错误记录"""
        # 记录错误
        error = ConnectionError("Network failed")
        self.error_handler.log_error("binance", error, 2)
        
        # 检查错误统计
        stats = self.error_handler.get_error_stats("binance")
        assert stats["total_errors"] == 1
        assert stats["error_types"]["network_error"] == 1
        assert stats["retry_count"] == 2
        assert stats["last_error"]["type"] == "network_error"
        
        # 记录多个错误
        self.error_handler.log_error("binance", TimeoutError("Timeout"), 1)
        stats = self.error_handler.get_error_stats("binance")
        assert stats["total_errors"] == 2
        assert stats["error_types"]["network_error"] == 1
        assert stats["error_types"]["timeout_error"] == 1

class TestAPIRequestHandler:
    """API请求处理器测试"""
    
    def setup_method(self):
        """设置测试环境"""
        self.rate_limit_configs = [
            RateLimitConfig(RateLimitType.REQUESTS_PER_SECOND, 2, 1),
            RateLimitConfig(RateLimitType.REQUESTS_PER_MINUTE, 10, 60)
        ]
        
        self.retry_config = RetryConfig(
            max_retries=2,
            retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=0.1,  # 短延迟用于测试
            max_delay=1.0
        )
        
        self.request_handler = APIRequestHandler(self.rate_limit_configs, self.retry_config)
    
    @pytest.mark.asyncio
    async def test_successful_request(self):
        """测试成功请求"""
        # 模拟成功的API调用
        async def mock_api_call():
            return {"success": True, "data": "test_data"}
        
        response = await self.request_handler.execute_request(mock_api_call, "binance")
        
        # 验证响应
        assert isinstance(response, APIResponse)
        assert response.success is True
        assert response.data == {"success": True, "data": "test_data"}
        assert response.retry_count == 0
        assert response.response_time > 0
    
    @pytest.mark.asyncio
    async def test_failed_request_with_retry(self):
        """测试失败请求的重试"""
        call_count = 0
        
        async def mock_failing_api_call():
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # 前两次失败
                raise ConnectionError("Network failed")
            return {"success": True, "data": "retry_success"}
        
        response = await self.request_handler.execute_request(mock_failing_api_call, "binance")
        
        # 验证重试成功
        assert response.success is True
        assert response.data == {"success": True, "data": "retry_success"}
        assert response.retry_count == 2  # 重试了2次
        assert call_count == 3  # 总共调用了3次
    
    @pytest.mark.asyncio
    async def test_failed_request_no_retry(self):
        """测试不可重试的失败请求"""
        async def mock_auth_error_call():
            raise Exception("Unauthorized access")
        
        response = await self.request_handler.execute_request(mock_auth_error_call, "binance")
        
        # 验证没有重试
        assert response.success is False
        assert response.retry_count == 0
        assert "Unauthorized" in response.error
        assert response.error_type == ErrorType.AUTHENTICATION_ERROR
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """测试限流功能"""
        async def mock_api_call():
            return {"success": True}
        
        # 快速发送多个请求
        responses = []
        for i in range(5):
            response = await self.request_handler.execute_request(mock_api_call, "binance")
            responses.append(response)
        
        # 验证有些请求因为限流而失败
        failed_responses = [r for r in responses if not r.success]
        assert len(failed_responses) > 0
        
        # 检查是否有限流错误
        rate_limited = any("Rate limit exceeded" in str(r.error) for r in failed_responses)
        assert rate_limited

class TestExchangeAPIWrapper:
    """交易所API包装器测试"""
    
    def setup_method(self):
        """设置测试环境"""
        # 创建模拟适配器
        self.mock_adapter = Mock(spec=ExchangeAdapter)
        self.mock_adapter.name = "binance"
        self.mock_adapter.get_ticker = AsyncMock()
        self.mock_adapter.get_balance = AsyncMock()
        self.mock_adapter.place_order = AsyncMock()
        
        # 创建API包装器
        rate_limit_configs = [
            RateLimitConfig(RateLimitType.REQUESTS_PER_SECOND, 5, 1)
        ]
        
        retry_config = RetryConfig(
            max_retries=2,
            retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=0.1,
            max_delay=1.0
        )
        
        self.wrapper = ExchangeAPIWrapper(self.mock_adapter, rate_limit_configs, retry_config)
    
    @pytest.mark.asyncio
    async def test_successful_api_calls(self):
        """测试成功的API调用"""
        # 设置模拟返回值
        self.mock_adapter.get_ticker.return_value = {"symbol": "BTCUSDT", "price": 50000}
        self.mock_adapter.get_balance.return_value = {"BTC": 1.0, "USDT": 10000}
        
        # 测试获取行情
        response = await self.wrapper.get_ticker("BTCUSDT")
        assert response.success is True
        assert response.data["symbol"] == "BTCUSDT"
        
        # 测试获取余额
        response = await self.wrapper.get_balance()
        assert response.success is True
        assert response.data["BTC"] == 1.0
        
        # 验证统计信息
        stats = self.wrapper.get_stats()
        assert stats["total_requests"] == 2
        assert stats["successful_requests"] == 2
        assert stats["failed_requests"] == 0
        assert stats["success_rate"] == 1.0
    
    @pytest.mark.asyncio
    async def test_failed_api_calls(self):
        """测试失败的API调用"""
        # 设置模拟失败
        self.mock_adapter.get_ticker.side_effect = ConnectionError("Network failed")
        
        # 测试获取行情失败
        response = await self.wrapper.get_ticker("BTCUSDT")
        assert response.success is False
        assert response.retry_count > 0
        assert response.error_type == ErrorType.NETWORK_ERROR
        
        # 验证统计信息
        stats = self.wrapper.get_stats()
        assert stats["total_requests"] == 1
        assert stats["successful_requests"] == 0
        assert stats["failed_requests"] == 1
        assert stats["success_rate"] == 0.0

class TestExchangeAPIManager:
    """交易所API管理器测试"""
    
    def setup_method(self):
        """设置测试环境"""
        # 创建临时配置文件
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        config_content = """
binance:
  type: "binance"
  name: "Binance"
  api_key: "test_key"
  api_secret: "test_secret"
  base_url: "https://api.binance.com"
  symbols:
    - "BTCUSDT"
  enabled: true

gateio:
  type: "gateio"
  name: "Gate.io"
  api_key: "test_key"
  api_secret: "test_secret"
  base_url: "https://api.gateio.ws"
  symbols:
    - "BTC_USDT"
  enabled: true

common:
  timeout: 10
"""
        self.temp_config.write(config_content)
        self.temp_config.flush()
        
        # 创建配置管理器
        self.config_manager = ExchangeConfigManager(self.temp_config.name)
        self.config = self.config_manager.load_config()
        
        # 创建模拟适配器
        self.mock_adapter1 = Mock(spec=ExchangeAdapter)
        self.mock_adapter1.name = "binance"
        self.mock_adapter1.get_ticker = AsyncMock()
        
        self.mock_adapter2 = Mock(spec=ExchangeAdapter)
        self.mock_adapter2.name = "gateio"
        self.mock_adapter2.get_ticker = AsyncMock()
        
        # 添加模拟适配器
        self.config_manager.exchange_adapters = {
            "binance": self.mock_adapter1,
            "gateio": self.mock_adapter2
        }
        
        # 创建API管理器
        self.api_manager = ExchangeAPIManager(self.config_manager)
    
    def teardown_method(self):
        """清理测试环境"""
        self.temp_config.close()
        os.unlink(self.temp_config.name)
    
    def test_wrapper_initialization(self):
        """测试包装器初始化"""
        # 验证包装器已创建
        assert "binance" in self.api_manager.wrappers
        assert "gateio" in self.api_manager.wrappers
        
        # 验证包装器属性
        binance_wrapper = self.api_manager.get_wrapper("binance")
        assert binance_wrapper.exchange_name == "binance"
        
        gateio_wrapper = self.api_manager.get_wrapper("gateio")
        assert gateio_wrapper.exchange_name == "gateio"
    
    def test_get_all_stats(self):
        """测试获取所有统计信息"""
        all_stats = self.api_manager.get_all_stats()
        
        # 验证统计信息结构
        assert "binance" in all_stats
        assert "gateio" in all_stats
        
        # 验证统计信息内容
        binance_stats = all_stats["binance"]
        assert "exchange_name" in binance_stats
        assert "total_requests" in binance_stats
        assert "success_rate" in binance_stats
        assert "rate_limit_status" in binance_stats
        assert "error_stats" in binance_stats
    
    def test_config_updates(self):
        """测试配置更新"""
        # 更新限流配置
        new_rate_configs = [
            RateLimitConfig(RateLimitType.REQUESTS_PER_SECOND, 20, 1)
        ]
        
        self.api_manager.update_rate_limit_config("binance", new_rate_configs)
        
        # 更新重试配置
        new_retry_config = RetryConfig(
            max_retries=5,
            retry_strategy=RetryStrategy.LINEAR_BACKOFF,
            base_delay=2.0,
            max_delay=30.0
        )
        
        self.api_manager.update_retry_config("binance", new_retry_config)
        
        # 验证配置已更新
        wrapper = self.api_manager.get_wrapper("binance")
        assert wrapper is not None

@pytest.mark.asyncio
async def test_api_rate_limiter_integration():
    """API限流器集成测试"""
    """测试API限流和错误处理的完整流程"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config_content = """
binance:
  type: "binance"
  name: "Binance"
  api_key: "test_key"
  api_secret: "test_secret"
  base_url: "https://api.binance.com"
  symbols:
    - "BTCUSDT"
  enabled: true

common:
  timeout: 10
"""
        f.write(config_content)
        f.flush()
        
        try:
            # 创建配置管理器
            config_manager = ExchangeConfigManager(f.name)
            config = config_manager.load_config()
            
            # 创建模拟适配器
            mock_adapter = Mock(spec=ExchangeAdapter)
            mock_adapter.name = "binance"
            mock_adapter.get_ticker = AsyncMock()
            
            # 添加模拟适配器
            config_manager.exchange_adapters = {
                "binance": mock_adapter
            }
            
            # 创建API管理器
            api_manager = ExchangeAPIManager(config_manager)
            
            # 验证包装器创建
            wrapper = api_manager.get_wrapper("binance")
            assert wrapper is not None
            assert wrapper.exchange_name == "binance"
            
            # 验证限流配置
            rate_limit_status = wrapper.request_handler.get_rate_limit_status("binance")
            assert "token_bucket_0" in rate_limit_status
            
            # 验证错误处理器
            error_handler = wrapper.request_handler.error_handler
            assert error_handler.retry_config.max_retries == 3
            
            # 验证统计信息
            stats = api_manager.get_all_stats()
            assert "binance" in stats
            assert stats["binance"]["exchange_name"] == "binance"
            
        finally:
            os.unlink(f.name)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])