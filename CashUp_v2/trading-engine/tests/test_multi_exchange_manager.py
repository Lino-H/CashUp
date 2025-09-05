"""
多交易所支持测试
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock

from services.multi_exchange_manager import (
    MultiExchangeManager, ExchangeRequest, ExchangeResponse, ParallelRequestResult,
    MultiExchangeDataFetcher, MultiExchangeOrderManager, MultiExchangeArbitrage
)
from config.exchange_config import ExchangeConfigManager, ExchangeConfig
from exchanges.base import Ticker, Balance, Order, Kline, OrderSide, OrderType

class TestMultiExchangeManager:
    """多交易所管理器测试"""
    
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
  retry_count: 2
"""
        self.temp_config.write(config_content)
        self.temp_config.flush()
        
        # 创建配置管理器
        self.config_manager = ExchangeConfigManager(self.temp_config.name)
        self.config = self.config_manager.load_config()
        
        # 创建多交易所管理器
        self.multi_manager = MultiExchangeManager(self.config_manager)
        
        # 模拟交易所适配器
        self.mock_adapter1 = Mock()
        self.mock_adapter1.get_ticker = AsyncMock()
        self.mock_adapter1.get_balance = AsyncMock()
        self.mock_adapter1.get_orders = AsyncMock()
        
        self.mock_adapter2 = Mock()
        self.mock_adapter2.get_ticker = AsyncMock()
        self.mock_adapter2.get_balance = AsyncMock()
        self.mock_adapter2.get_orders = AsyncMock()
        
        # 添加模拟适配器
        self.config_manager.exchange_adapters = {
            "binance": self.mock_adapter1,
            "gateio": self.mock_adapter2
        }
    
    def teardown_method(self):
        """清理测试环境"""
        self.temp_config.close()
        os.unlink(self.temp_config.name)
    
    @pytest.mark.asyncio
    async def test_execute_parallel_requests_success(self):
        """测试并行请求成功"""
        # 设置模拟返回值
        self.mock_adapter1.get_ticker.return_value = Ticker(
            symbol="BTCUSDT", last_price=50000.0, bid_price=49900.0, 
            ask_price=50100.0, bid_volume=1.0, ask_volume=1.0,
            volume_24h=1000.0, high_24h=51000.0, low_24h=49000.0,
            price_change_24h=1000.0, price_change_percent_24h=2.0,
            timestamp=asyncio.get_event_loop().time()
        )
        
        self.mock_adapter2.get_ticker.return_value = Ticker(
            symbol="BTC_USDT", last_price=50050.0, bid_price=49950.0,
            ask_price=50150.0, bid_volume=1.0, ask_volume=1.0,
            volume_24h=1000.0, high_24h=51000.0, low_24h=49000.0,
            price_change_24h=1000.0, price_change_percent_24h=2.0,
            timestamp=asyncio.get_event_loop().time()
        )
        
        # 创建请求
        requests = [
            ExchangeRequest("binance", "get_ticker", {"symbol": "BTCUSDT"}),
            ExchangeRequest("gateio", "get_ticker", {"symbol": "BTC_USDT"})
        ]
        
        # 执行并行请求
        result = await self.multi_manager.execute_parallel_requests(requests)
        
        # 验证结果
        assert isinstance(result, ParallelRequestResult)
        assert len(result.successful_requests) == 2
        assert len(result.failed_requests) == 0
        assert result.success_rate == 1.0
        assert result.total_time > 0
        
        # 验证响应内容
        assert result.successful_requests[0].exchange_name == "binance"
        assert result.successful_requests[0].success is True
        assert result.successful_requests[0].data.symbol == "BTCUSDT"
        
        assert result.successful_requests[1].exchange_name == "gateio"
        assert result.successful_requests[1].success is True
        assert result.successful_requests[1].data.symbol == "BTC_USDT"
    
    @pytest.mark.asyncio
    async def test_execute_parallel_requests_with_failure(self):
        """测试并行请求包含失败的情况"""
        # 设置模拟返回值 - 一个成功，一个失败
        self.mock_adapter1.get_ticker.return_value = Ticker(
            symbol="BTCUSDT", last_price=50000.0, bid_price=49900.0,
            ask_price=50100.0, bid_volume=1.0, ask_volume=1.0,
            volume_24h=1000.0, high_24h=51000.0, low_24h=49000.0,
            price_change_24h=1000.0, price_change_percent_24h=2.0,
            timestamp=asyncio.get_event_loop().time()
        )
        
        self.mock_adapter2.get_ticker.side_effect = Exception("API Error")
        
        # 创建请求
        requests = [
            ExchangeRequest("binance", "get_ticker", {"symbol": "BTCUSDT"}),
            ExchangeRequest("gateio", "get_ticker", {"symbol": "BTC_USDT"})
        ]
        
        # 执行并行请求
        result = await self.multi_manager.execute_parallel_requests(requests)
        
        # 验证结果
        assert isinstance(result, ParallelRequestResult)
        assert len(result.successful_requests) == 1
        assert len(result.failed_requests) == 1
        assert result.success_rate == 0.5
        
        # 验证成功请求
        assert result.successful_requests[0].exchange_name == "binance"
        assert result.successful_requests[0].success is True
        
        # 验证失败请求
        assert result.failed_requests[0].exchange_name == "gateio"
        assert result.failed_requests[0].success is False
        assert "API Error" in result.failed_requests[0].error
    
    @pytest.mark.asyncio
    async def test_execute_parallel_requests_timeout(self):
        """测试请求超时"""
        # 设置模拟返回值 - 超时
        async def slow_ticker():
            await asyncio.sleep(2)  # 模拟延迟
            return Ticker(
                symbol="BTCUSDT", last_price=50000.0, bid_price=49900.0,
                ask_price=50100.0, bid_volume=1.0, ask_volume=1.0,
                volume_24h=1000.0, high_24h=51000.0, low_24h=49000.0,
                price_change_24h=1000.0, price_change_percent_24h=2.0,
                timestamp=asyncio.get_event_loop().time()
            )
        
        self.mock_adapter1.get_ticker = slow_ticker
        
        # 创建请求 - 设置短超时
        requests = [
            ExchangeRequest("binance", "get_ticker", {"symbol": "BTCUSDT"}, timeout=0.5)
        ]
        
        # 执行并行请求
        result = await self.multi_manager.execute_parallel_requests(requests)
        
        # 验证结果
        assert len(result.successful_requests) == 0
        assert len(result.failed_requests) == 1
        assert result.success_rate == 0.0
        
        # 验证超时错误
        assert result.failed_requests[0].exchange_name == "binance"
        assert result.failed_requests[0].success is False
        assert "超时" in result.failed_requests[0].error
    
    def test_request_stats(self):
        """测试请求统计"""
        # 初始状态应该没有统计信息
        stats = self.multi_manager.get_request_stats()
        assert len(stats) == 0
        
        # 模拟更新统计
        self.multi_manager._update_stats("binance", "get_ticker", True, 0.5)
        self.multi_manager._update_stats("binance", "get_ticker", False, 1.0)
        
        # 验证统计信息
        stats = self.multi_manager.get_request_stats()
        assert "binance.get_ticker" in stats
        
        binance_stats = stats["binance.get_ticker"]
        assert binance_stats["total_requests"] == 2
        assert binance_stats["successful_requests"] == 1
        assert binance_stats["failed_requests"] == 1
        assert binance_stats["total_response_time"] == 1.5
        assert binance_stats["avg_response_time"] == 0.75
        assert binance_stats["success_rate"] == 0.5
        
        # 重置统计
        self.multi_manager.reset_stats()
        stats = self.multi_manager.get_request_stats()
        assert len(stats) == 0

class TestMultiExchangeDataFetcher:
    """多交易所数据获取器测试"""
    
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
        
        # 创建多交易所管理器
        self.multi_manager = MultiExchangeManager(self.config_manager)
        
        # 创建数据获取器
        self.data_fetcher = MultiExchangeDataFetcher(self.multi_manager)
        
        # 模拟交易所适配器
        self.mock_adapter1 = Mock()
        self.mock_adapter1.get_ticker = AsyncMock()
        self.mock_adapter1.get_balance = AsyncMock()
        
        self.mock_adapter2 = Mock()
        self.mock_adapter2.get_ticker = AsyncMock()
        self.mock_adapter2.get_balance = AsyncMock()
        
        # 添加模拟适配器
        self.config_manager.exchange_adapters = {
            "binance": self.mock_adapter1,
            "gateio": self.mock_adapter2
        }
    
    def teardown_method(self):
        """清理测试环境"""
        self.temp_config.close()
        os.unlink(self.temp_config.name)
    
    @pytest.mark.asyncio
    async def test_get_tickers_from_all_exchanges(self):
        """测试从所有交易所获取行情"""
        # 设置模拟返回值
        self.mock_adapter1.get_ticker.return_value = Ticker(
            symbol="BTCUSDT", last_price=50000.0, bid_price=49900.0,
            ask_price=50100.0, bid_volume=1.0, ask_volume=1.0,
            volume_24h=1000.0, high_24h=51000.0, low_24h=49000.0,
            price_change_24h=1000.0, price_change_percent_24h=2.0,
            timestamp=asyncio.get_event_loop().time()
        )
        
        self.mock_adapter2.get_ticker.return_value = Ticker(
            symbol="BTC_USDT", last_price=50050.0, bid_price=49950.0,
            ask_price=50150.0, bid_volume=1.0, ask_volume=1.0,
            volume_24h=1000.0, high_24h=51000.0, low_24h=49000.0,
            price_change_24h=1000.0, price_change_percent_24h=2.0,
            timestamp=asyncio.get_event_loop().time()
        )
        
        # 获取行情
        tickers = await self.data_fetcher.get_tickers_from_all_exchanges("BTCUSDT")
        
        # 验证结果
        assert len(tickers) == 2
        assert "binance" in tickers
        assert "gateio" in tickers
        
        assert tickers["binance"].symbol == "BTCUSDT"
        assert tickers["binance"].last_price == 50000.0
        
        assert tickers["gateio"].symbol == "BTC_USDT"
        assert tickers["gateio"].last_price == 50050.0
    
    @pytest.mark.asyncio
    async def test_get_balances_from_all_exchanges(self):
        """测试从所有交易所获取余额"""
        # 设置模拟返回值
        self.mock_adapter1.get_balance.return_value = {
            "BTC": Balance(asset="BTC", free=1.0, used=0.5, total=1.5),
            "USDT": Balance(asset="USDT", free=10000.0, used=5000.0, total=15000.0)
        }
        
        self.mock_adapter2.get_balance.return_value = {
            "BTC": Balance(asset="BTC", free=2.0, used=1.0, total=3.0),
            "USDT": Balance(asset="USDT", free=20000.0, used=10000.0, total=30000.0)
        }
        
        # 获取余额
        balances = await self.data_fetcher.get_balances_from_all_exchanges()
        
        # 验证结果
        assert len(balances) == 2
        assert "binance" in balances
        assert "gateio" in balances
        
        assert balances["binance"]["BTC"].total == 1.5
        assert balances["binance"]["USDT"].total == 15000.0
        
        assert balances["gateio"]["BTC"].total == 3.0
        assert balances["gateio"]["USDT"].total == 30000.0

class TestMultiExchangeOrderManager:
    """多交易所订单管理器测试"""
    
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
        
        # 创建多交易所管理器
        self.multi_manager = MultiExchangeManager(self.config_manager)
        
        # 创建订单管理器
        self.order_manager = MultiExchangeOrderManager(self.multi_manager)
        
        # 模拟交易所适配器
        self.mock_adapter1 = Mock()
        self.mock_adapter1.get_ticker = AsyncMock()
        self.mock_adapter1.place_order = AsyncMock()
        
        self.mock_adapter2 = Mock()
        self.mock_adapter2.get_ticker = AsyncMock()
        self.mock_adapter2.place_order = AsyncMock()
        
        # 添加模拟适配器
        self.config_manager.exchange_adapters = {
            "binance": self.mock_adapter1,
            "gateio": self.mock_adapter2
        }
    
    def teardown_method(self):
        """清理测试环境"""
        self.temp_config.close()
        os.unlink(self.temp_config.name)
    
    @pytest.mark.asyncio
    async def test_place_order_on_best_exchange(self):
        """测试在最优交易所下单"""
        # 设置模拟返回值 - Gate.io价格更优
        self.mock_adapter1.get_ticker.return_value = Ticker(
            symbol="BTCUSDT", last_price=50000.0, bid_price=49900.0,
            ask_price=50100.0, bid_volume=1.0, ask_volume=1.0,
            volume_24h=1000.0, high_24h=51000.0, low_24h=49000.0,
            price_change_24h=1000.0, price_change_percent_24h=2.0,
            timestamp=asyncio.get_event_loop().time()
        )
        
        self.mock_adapter2.get_ticker.return_value = Ticker(
            symbol="BTC_USDT", last_price=49900.0, bid_price=49800.0,
            ask_price=50000.0, bid_volume=1.0, ask_volume=1.0,
            volume_24h=1000.0, high_24h=51000.0, low_24h=49000.0,
            price_change_24h=1000.0, price_change_percent_24h=2.0,
            timestamp=asyncio.get_event_loop().time()
        )
        
        # 设置下单返回值
        from exchanges.base import OrderRequest, Order
        mock_order = Order(
            id="12345", client_order_id="client123", symbol="BTCUSDT",
            side=OrderSide.BUY, type=OrderType.MARKET, quantity=0.001,
            price=None, stop_price=None, time_in_force=None,
            status=None, filled_quantity=0.0, remaining_quantity=0.001,
            average_price=None, commission=0.0, created_at=asyncio.get_event_loop().time(),
            updated_at=asyncio.get_event_loop().time(), exchange="binance"
        )
        self.mock_adapter2.place_order.return_value = mock_order
        
        # 创建订单请求
        order_request = OrderRequest(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            quantity=0.001
        )
        
        # 在最优交易所下单
        result = await self.order_manager.place_order_on_best_exchange(order_request)
        
        # 验证结果
        assert result["success"] is True
        assert result["exchange"] == "gateio"
        assert result["order"] == mock_order
        assert result["price"] == 50000.0
        
        # 验证调用了正确的适配器
        self.mock_adapter2.place_order.assert_called_once()
        self.mock_adapter1.place_order.assert_not_called()

class TestMultiExchangeArbitrage:
    """多交易所套利测试"""
    
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
        
        # 创建多交易所管理器
        self.multi_manager = MultiExchangeManager(self.config_manager)
        
        # 创建套利模块
        self.arbitrage = MultiExchangeArbitrage(self.multi_manager)
        
        # 模拟交易所适配器
        self.mock_adapter1 = Mock()
        self.mock_adapter1.get_ticker = AsyncMock()
        self.mock_adapter1.place_order = AsyncMock()
        
        self.mock_adapter2 = Mock()
        self.mock_adapter2.get_ticker = AsyncMock()
        self.mock_adapter2.place_order = AsyncMock()
        
        # 添加模拟适配器
        self.config_manager.exchange_adapters = {
            "binance": self.mock_adapter1,
            "gateio": self.mock_adapter2
        }
    
    def teardown_method(self):
        """清理测试环境"""
        self.temp_config.close()
        os.unlink(self.temp_config.name)
    
    @pytest.mark.asyncio
    async def test_find_arbitrage_opportunities(self):
        """测试寻找套利机会"""
        # 设置模拟返回值 - 存在套利机会
        self.mock_adapter1.get_ticker.return_value = Ticker(
            symbol="BTCUSDT", last_price=50000.0, bid_price=49900.0,
            ask_price=50100.0, bid_volume=1.0, ask_volume=1.0,
            volume_24h=1000.0, high_24h=51000.0, low_24h=49000.0,
            price_change_24h=1000.0, price_change_percent_24h=2.0,
            timestamp=asyncio.get_event_loop().time()
        )
        
        self.mock_adapter2.get_ticker.return_value = Ticker(
            symbol="BTC_USDT", last_price=50200.0, bid_price=50100.0,
            ask_price=50300.0, bid_volume=1.0, ask_volume=1.0,
            volume_24h=1000.0, high_24h=51000.0, low_24h=49000.0,
            price_change_24h=1000.0, price_change_percent_24h=2.0,
            timestamp=asyncio.get_event_loop().time()
        )
        
        # 寻找套利机会
        opportunities = await self.arbitrage.find_arbitrage_opportunities("BTCUSDT", 0.001)
        
        # 验证结果
        assert len(opportunities) == 2  # 两个方向的套利机会
        
        # 验证套利机会（从Binance买入，Gate.io卖出）
        opportunity1 = opportunities[0]
        assert opportunity1["buy_exchange"] == "binance"
        assert opportunity1["sell_exchange"] == "gateio"
        assert opportunity1["buy_price"] == 50100.0
        assert opportunity1["sell_price"] == 50100.0
        assert opportunity1["profit_rate"] == 0.0  # 价格相同，无套利
        
        # 验证套利机会（从Gate.io买入，Binance卖出）
        opportunity2 = opportunities[1]
        assert opportunity2["buy_exchange"] == "gateio"
        assert opportunity2["sell_exchange"] == "binance"
        assert opportunity2["buy_price"] == 50300.0
        assert opportunity2["sell_price"] == 49900.0
        assert opportunity2["profit_rate"] < 0  # 亏损
    
    @pytest.mark.asyncio
    async def test_find_arbitrage_opportunities_with_profit(self):
        """测试寻找有利可图的套利机会"""
        # 设置模拟返回值 - 存在套利机会
        self.mock_adapter1.get_ticker.return_value = Ticker(
            symbol="BTCUSDT", last_price=50000.0, bid_price=49900.0,
            ask_price=50100.0, bid_volume=1.0, ask_volume=1.0,
            volume_24h=1000.0, high_24h=51000.0, low_24h=49000.0,
            price_change_24h=1000.0, price_change_percent_24h=2.0,
            timestamp=asyncio.get_event_loop().time()
        )
        
        self.mock_adapter2.get_ticker.return_value = Ticker(
            symbol="BTC_USDT", last_price=50500.0, bid_price=50400.0,
            ask_price=50600.0, bid_volume=1.0, ask_volume=1.0,
            volume_24h=1000.0, high_24h=51000.0, low_24h=49000.0,
            price_change_24h=1000.0, price_change_percent_24h=2.0,
            timestamp=asyncio.get_event_loop().time()
        )
        
        # 寻找套利机会
        opportunities = await self.arbitrage.find_arbitrage_opportunities("BTCUSDT", 0.001)
        
        # 验证结果
        assert len(opportunities) == 2
        
        # 验证有利可图的套利机会
        profitable_opportunities = [opp for opp in opportunities if opp["profit_rate"] > 0.001]
        assert len(profitable_opportunities) == 1
        
        opportunity = profitable_opportunities[0]
        assert opportunity["buy_exchange"] == "binance"
        assert opportunity["sell_exchange"] == "gateio"
        assert opportunity["profit_rate"] > 0.001

@pytest.mark.asyncio
async def test_multi_exchange_integration():
    """多交易所集成测试"""
    """测试多交易所支持的完整流程"""
    
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
  retry_count: 2
"""
        f.write(config_content)
        f.flush()
        
        try:
            # 创建配置管理器
            config_manager = ExchangeConfigManager(f.name)
            config = config_manager.load_config()
            
            # 创建多交易所管理器
            multi_manager = MultiExchangeManager(config_manager)
            
            # 测试并行请求
            requests = [
                ExchangeRequest("binance", "get_ticker", {"symbol": "BTCUSDT"}),
                ExchangeRequest("gateio", "get_ticker", {"symbol": "BTC_USDT"})
            ]
            
            # 由于没有真实的适配器，这里测试请求结构
            assert len(requests) == 2
            assert requests[0].exchange_name == "binance"
            assert requests[1].exchange_name == "gateio"
            
            # 测试统计功能
            multi_manager._update_stats("binance", "get_ticker", True, 0.5)
            stats = multi_manager.get_request_stats()
            assert "binance.get_ticker" in stats
            assert stats["binance.get_ticker"]["success_rate"] == 1.0
            
        finally:
            os.unlink(f.name)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])