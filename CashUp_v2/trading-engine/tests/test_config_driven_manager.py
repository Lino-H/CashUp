"""
配置驱动的交易所接入测试
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.exchange_config import (
    ExchangeConfigManager, ExchangeConfig, ExchangeGlobalConfig,
    CommonConfig, RiskControlConfig, MonitoringConfig
)
from services.config_driven_manager import (
    ConfigDrivenExchangeManager, ExchangeFactory, get_exchange_manager
)

class TestExchangeConfig:
    """交易所配置测试"""
    
    def test_exchange_config_creation(self):
        """测试交易所配置创建"""
        config = ExchangeConfig(
            type="binance",
            name="Binance",
            api_key="test_key",
            api_secret="test_secret",
            base_url="https://api.binance.com"
        )
        
        assert config.type == "binance"
        assert config.name == "Binance"
        assert config.api_key == "test_key"
        assert config.enabled is True
    
    def test_config_manager_with_temp_file(self):
        """测试配置管理器"""
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
    - "ETHUSDT"
  enabled: true

gateio:
  type: "gateio"
  name: "Gate.io"
  api_key: "test_key"
  api_secret: "test_secret"
  base_url: "https://api.gateio.ws"
  symbols:
    - "BTC_USDT"
    - "ETH_USDT"
  enabled: false

common:
  timeout: 30
  retry_count: 3
  log_level: "INFO"

risk_control:
  max_order_amount: 10000
  max_position_ratio: 0.8

monitoring:
  enabled: true
  interval: 60
"""
            f.write(config_content)
            f.flush()
            
            try:
                manager = ExchangeConfigManager(f.name)
                config = manager.load_config()
                
                assert len(config.exchanges) == 2
                assert "binance" in config.exchanges
                assert "gateio" in config.exchanges
                assert config.exchanges["binance"].enabled is True
                assert config.exchanges["gateio"].enabled is False
                assert config.common.timeout == 30
                assert config.risk_control.max_order_amount == 10000
                assert config.monitoring.enabled is True
                
                # 测试获取启用交易所
                enabled = manager.get_enabled_exchanges()
                assert len(enabled) == 1
                assert "binance" in enabled
                
                # 测试启用/禁用
                assert manager.enable_exchange("gateio") is True
                assert manager.is_exchange_enabled("gateio") is True
                assert manager.disable_exchange("gateio") is True
                assert manager.is_exchange_enabled("gateio") is False
                
            finally:
                os.unlink(f.name)
    
    def test_config_manager_default_config(self):
        """测试默认配置"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")  # 空文件
            f.flush()
            
            try:
                manager = ExchangeConfigManager(f.name)
                config = manager.load_config()
                
                assert len(config.exchanges) >= 2  # 至少有默认的Binance和Gate.io
                assert "binance" in config.exchanges
                assert "gateio" in config.exchanges
                
            finally:
                os.unlink(f.name)
    
    def test_config_validation(self):
        """测试配置验证"""
        manager = ExchangeConfigManager()
        
        # 创建无效配置
        config = ExchangeGlobalConfig()
        config.exchanges["invalid"] = ExchangeConfig(
            type="",  # 空类型
            name="",  # 空名称
            enabled=True,
            api_key="",  # 空密钥
            api_secret="",  # 空密钥
            base_url="",  # 空URL
            symbols=[]  # 空交易对
        )
        manager.config = config
        
        errors = manager.validate_config()
        assert len(errors) > 0
        assert any("类型不能为空" in error for error in errors)
        assert any("名称不能为空" in error for error in errors)

class TestExchangeFactory:
    """交易所工厂测试"""
    
    def test_get_supported_exchanges(self):
        """测试获取支持的交易所"""
        supported = ExchangeFactory.get_supported_exchanges()
        assert "binance" in supported
        assert "gateio" in supported
        assert isinstance(supported, list)
    
    def test_is_exchange_supported(self):
        """测试检查交易所支持"""
        assert ExchangeFactory.is_exchange_supported("binance") is True
        assert ExchangeFactory.is_exchange_supported("gateio") is True
        assert ExchangeFactory.is_exchange_supported("unsupported") is False
    
    def test_register_exchange(self):
        """测试注册交易所"""
        # 创建一个模拟的交易所类
        class MockExchange:
            def __init__(self, config):
                pass
        
        # 注册新交易所
        ExchangeFactory.register_exchange("mock", MockExchange)
        assert ExchangeFactory.is_exchange_supported("mock") is True
        
        # 清理
        ExchangeFactory._exchange_classes.pop("mock", None)
    
    def test_create_exchange_invalid_config(self):
        """测试创建无效配置的交易所"""
        config = ExchangeConfig(
            type="unsupported",  # 不支持的类型
            name="Unsupported",
            api_key="test_key",
            api_secret="test_secret"
        )
        
        exchange = ExchangeFactory.create_exchange(config)
        assert exchange is None

class TestConfigDrivenManager:
    """配置驱动的管理器测试"""
    
    @pytest.mark.asyncio
    async def test_manager_initialization(self):
        """测试管理器初始化"""
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
  enabled: false  # 禁用以避免真实API调用

common:
  timeout: 10
  retry_count: 1
"""
            f.write(config_content)
            f.flush()
            
            try:
                manager = ConfigDrivenExchangeManager(f.name)
                
                # 模拟初始化（不进行真实API调用）
                assert not manager.is_initialized
                assert len(manager.exchange_adapters) == 0
                
                # 由于没有真实的API密钥，初始化会失败，但不会抛出异常
                result = await manager.initialize()
                assert result is False  # 由于没有真实的API密钥，初始化失败
                
            finally:
                os.unlink(f.name)
    
    @pytest.mark.asyncio
    async def test_manager_without_config_file(self):
        """测试没有配置文件的管理器"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")  # 空文件
            f.flush()
            
            try:
                manager = ConfigDrivenExchangeManager(f.name)
                
                # 应该能够处理空配置文件
                result = await manager.initialize()
                assert isinstance(result, bool)
                
                # 应该有默认配置
                assert len(manager.config_manager.get_exchange_names()) >= 2
                
            finally:
                os.unlink(f.name)
    
    def test_get_exchange_info(self):
        """测试获取交易所信息"""
        manager = ConfigDrivenExchangeManager()
        
        # 没有初始化时应该返回None
        info = manager.get_exchange_info("binance")
        assert info is None
        
        # 获取所有信息应该返回空列表
        all_info = manager.get_all_exchanges_info()
        assert all_info == []
    
    def test_config_summary(self):
        """测试配置摘要"""
        manager = ConfigDrivenExchangeManager()
        summary = manager.get_config_summary()
        
        assert isinstance(summary, dict)
        assert "active_exchanges" in summary
        assert "exchange_status" in summary
        assert summary["active_exchanges"] == 0
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查"""
        manager = ConfigDrivenExchangeManager()
        
        # 没有启用交易所时的健康检查
        result = await manager.health_check()
        
        assert isinstance(result, dict)
        assert "timestamp" in result
        assert "total_exchanges" in result
        assert "healthy_exchanges" in result
        assert "unhealthy_exchanges" in result
        assert "details" in result
        
        assert result["total_exchanges"] == 0
        assert result["healthy_exchanges"] == 0
        assert result["unhealthy_exchanges"] == 0

class TestGlobalManager:
    """全局管理器测试"""
    
    def test_get_exchange_manager(self):
        """测试获取全局管理器"""
        # 清理全局实例
        import trading_engine.services.config_driven_manager
        trading_engine.services.config_driven_manager._exchange_manager = None
        
        manager = get_exchange_manager()
        assert isinstance(manager, ConfigDrivenExchangeManager)
        
        # 再次调用应该返回同一个实例
        manager2 = get_exchange_manager()
        assert manager is manager2
        
        # 清理
        trading_engine.services.config_driven_manager._exchange_manager = None
    
    @pytest.mark.asyncio
    async def test_initialize_global_manager(self):
        """测试初始化全局管理器"""
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
  enabled: false

common:
  timeout: 10
"""
            f.write(config_content)
            f.flush()
            
            try:
                # 清理全局实例
                import trading_engine.services.config_driven_manager
                trading_engine.services.config_driven_manager._exchange_manager = None
                
                manager = await initialize_exchange_manager(f.name)
                assert isinstance(manager, ConfigDrivenExchangeManager)
                
                # 验证全局实例已设置
                global_manager = get_exchange_manager()
                assert manager is global_manager
                
            finally:
                os.unlink(f.name)
                # 清理全局实例
                trading_engine.services.config_driven_manager._exchange_manager = None

@pytest.mark.asyncio
async def test_config_driven_integration():
    """配置驱动的交易所接入集成测试"""
    """测试配置驱动的交易所接入完整流程"""
    
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
    - "ETHUSDT"
  enabled: false

gateio:
  type: "gateio"
  name: "Gate.io"
  api_key: "test_key"
  api_secret: "test_secret"
  base_url: "https://api.gateio.ws"
  symbols:
    - "BTC_USDT"
    - "ETH_USDT"
  enabled: false

common:
  timeout: 10
  retry_count: 2
  log_level: "DEBUG"

risk_control:
  max_order_amount: 5000
  max_position_ratio: 0.5

monitoring:
  enabled: true
  interval: 30
  alert_threshold:
    error_rate: 0.1
    response_time: 10
"""
        f.write(config_content)
        f.flush()
        
        try:
            # 创建管理器
            manager = ConfigDrivenExchangeManager(f.name)
            
            # 测试配置加载
            config_summary = manager.get_config_summary()
            assert config_summary["total_exchanges"] >= 2
            assert config_summary["active_exchanges"] == 0
            
            # 测试配置管理
            assert manager.config_manager.is_exchange_enabled("binance") is False
            assert manager.config_manager.enable_exchange("binance") is True
            assert manager.config_manager.is_exchange_enabled("binance") is True
            
            # 测试健康检查（无连接）
            health = await manager.health_check()
            assert health["total_exchanges"] == 0
            assert health["healthy_exchanges"] == 0
            
            # 测试配置保存
            assert await manager.save_config() is True
            
            # 测试重新加载配置
            assert await manager.reload_config() is True
            
        finally:
            os.unlink(f.name)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])