"""
交易所监控和切换测试
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta

from services.exchange_monitoring import (
    ExchangeMonitor, ExchangeSwitcher, ExchangeMonitoringService,
    ExchangeHealthStatus, AlertLevel, Alert, ExchangeMetrics,
    HealthCheckResult
)
from config.exchange_config import ExchangeConfigManager, ExchangeConfig
from exchanges.base import ExchangeAdapter

class TestExchangeMonitor:
    """交易所监控器测试"""
    
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
        
        # 创建监控器
        self.monitor = ExchangeMonitor(self.config_manager)
        
        # 模拟交易所适配器
        self.mock_adapter1 = Mock(spec=ExchangeAdapter)
        self.mock_adapter1.test_connection = AsyncMock()
        self.mock_adapter1.get_server_time = AsyncMock()
        
        self.mock_adapter2 = Mock(spec=ExchangeAdapter)
        self.mock_adapter2.test_connection = AsyncMock()
        self.mock_adapter2.get_server_time = AsyncMock()
        
        # 添加模拟适配器
        self.config_manager.exchange_adapters = {
            "binance": self.mock_adapter1,
            "gateio": self.mock_adapter2
        }
        
        # 设置较短的检查间隔用于测试
        self.monitor.check_interval = 1
    
    def teardown_method(self):
        """清理测试环境"""
        if self.monitor.is_monitoring:
            asyncio.run(self.monitor.stop_monitoring())
        self.temp_config.close()
        os.unlink(self.temp_config.name)
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self):
        """测试启动和停止监控"""
        # 启动监控
        await self.monitor.start_monitoring()
        assert self.monitor.is_monitoring is True
        assert self.monitor.monitor_task is not None
        
        # 等待一下让监控任务开始
        await asyncio.sleep(0.1)
        
        # 停止监控
        await self.monitor.stop_monitoring()
        assert self.monitor.is_monitoring is False
    
    @pytest.mark.asyncio
    async def test_check_exchange_health_healthy(self):
        """测试健康交易所检查"""
        # 设置模拟返回值 - 健康状态
        self.mock_adapter1.test_connection.return_value = True
        self.mock_adapter1.get_server_time.return_value = datetime.now()
        
        # 执行健康检查
        result = await self.monitor._check_exchange_health("binance")
        
        # 验证结果
        assert isinstance(result, HealthCheckResult)
        assert result.exchange_name == "binance"
        assert result.status == ExchangeHealthStatus.HEALTHY
        assert len(result.issues) == 0
        assert result.metrics.connection_status is True
        assert result.metrics.success_rate == 1.0
        
        # 验证健康状态已更新
        assert self.monitor.health_status["binance"] == ExchangeHealthStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_check_exchange_health_offline(self):
        """测试离线交易所检查"""
        # 设置模拟返回值 - 离线状态
        self.mock_adapter1.test_connection.return_value = False
        
        # 执行健康检查
        result = await self.monitor._check_exchange_health("binance")
        
        # 验证结果
        assert result.status == ExchangeHealthStatus.OFFLINE
        assert len(result.issues) > 0
        assert result.metrics.connection_status is False
        assert result.metrics.error_count > 0
        
        # 验证生成了告警
        alerts = self.monitor.get_alerts(exchange_name="binance")
        assert len(alerts) > 0
        assert alerts[0].level == AlertLevel.CRITICAL
        assert "离线" in alerts[0].title
    
    @pytest.mark.asyncio
    async def test_check_exchange_health_slow_response(self):
        """测试响应慢的交易所检查"""
        # 设置模拟返回值 - 响应慢但正常
        async def slow_connection():
            await asyncio.sleep(0.1)  # 模拟延迟
            return True
        
        self.mock_adapter1.test_connection = slow_connection
        self.mock_adapter1.get_server_time = AsyncMock()
        
        # 设置较低的响应时间阈值
        self.monitor.response_time_threshold = 0.05
        
        # 执行健康检查
        result = await self.monitor._check_exchange_health("binance")
        
        # 验证结果
        assert result.status == ExchangeHealthStatus.DEGRADED
        assert result.metrics.response_time > 0.05
        
        # 验证生成了告警
        alerts = self.monitor.get_alerts(exchange_name="binance")
        assert len(alerts) > 0
        assert alerts[0].level == AlertLevel.WARNING
        assert "性能下降" in alerts[0].title
    
    @pytest.mark.asyncio
    async def test_check_exchange_health_api_error(self):
        """测试API错误的交易所检查"""
        # 设置模拟返回值 - API错误
        self.mock_adapter1.test_connection.return_value = True
        self.mock_adapter1.get_server_time.side_effect = Exception("API Error")
        
        # 执行健康检查
        result = await self.monitor._check_exchange_health("binance")
        
        # 验证结果
        assert result.status == ExchangeHealthStatus.UNHEALTHY
        assert len(result.issues) > 0
        assert "API调用失败" in result.issues[0]
    
    def test_alert_management(self):
        """测试告警管理"""
        # 创建测试告警
        alert = Alert(
            id="test_alert",
            exchange_name="binance",
            level=AlertLevel.WARNING,
            title="测试告警",
            message="这是一个测试告警"
        )
        
        # 添加告警
        self.monitor.alerts.append(alert)
        
        # 获取告警
        alerts = self.monitor.get_alerts()
        assert len(alerts) == 1
        assert alerts[0].id == "test_alert"
        
        # 按交易所过滤
        binance_alerts = self.monitor.get_alerts(exchange_name="binance")
        assert len(binance_alerts) == 1
        
        gateio_alerts = self.monitor.get_alerts(exchange_name="gateio")
        assert len(gateio_alerts) == 0
        
        # 按级别过滤
        warning_alerts = self.monitor.get_alerts(level=AlertLevel.WARNING)
        assert len(warning_alerts) == 1
        
        error_alerts = self.monitor.get_alerts(level=AlertLevel.ERROR)
        assert len(error_alerts) == 0
        
        # 解决告警
        resolved = self.monitor.resolve_alert("test_alert")
        assert resolved is True
        
        # 验证告警已解决
        unresolved_alerts = self.monitor.get_alerts(resolved=False)
        assert len(unresolved_alerts) == 0
        
        resolved_alerts = self.monitor.get_alerts(resolved=True)
        assert len(resolved_alerts) == 1
    
    def test_alert_callback(self):
        """测试告警回调"""
        callback_called = False
        received_alert = None
        
        def test_callback(alert):
            nonlocal callback_called, received_alert
            callback_called = True
            received_alert = alert
        
        # 添加回调
        self.monitor.add_alert_callback(test_callback)
        
        # 创建告警
        alert = Alert(
            id="callback_test",
            exchange_name="binance",
            level=AlertLevel.INFO,
            title="回调测试",
            message="测试回调功能"
        )
        
        # 手动调用通知函数
        asyncio.run(self.monitor._notify_alert(alert))
        
        # 验证回调被调用
        assert callback_called is True
        assert received_alert is not None
        assert received_alert.id == "callback_test"
        
        # 移除回调
        self.monitor.remove_alert_callback(test_callback)
        assert len(self.monitor.alert_callbacks) == 0
    
    def test_alert_frequency_limiting(self):
        """测试告警频率限制"""
        # 创建相同类型的多个告警
        for i in range(3):
            alert = Alert(
                id=f"frequency_test_{i}",
                exchange_name="binance",
                level=AlertLevel.WARNING,
                title="频率测试",
                message=f"测试告警 {i}"
            )
            
            # 检查是否应该发送告警
            should_send = self.monitor._should_send_alert(alert)
            
            if i == 0:
                assert should_send is True
            else:
                # 后续的告警应该被频率限制
                assert should_send is False
    
    def test_health_status_retrieval(self):
        """测试健康状态获取"""
        # 设置一些健康状态
        self.monitor.health_status["binance"] = ExchangeHealthStatus.HEALTHY
        self.monitor.health_status["gateio"] = ExchangeHealthStatus.DEGRADED
        
        # 获取所有健康状态
        all_status = self.monitor.get_health_status()
        assert len(all_status) == 2
        assert all_status["binance"]["status"] == "healthy"
        assert all_status["gateio"]["status"] == "degraded"
        
        # 获取单个交易所健康状态
        binance_status = self.monitor.get_health_status("binance")
        assert binance_status["exchange_name"] == "binance"
        assert binance_status["status"] == "healthy"

class TestExchangeSwitcher:
    """交易所切换器测试"""
    
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
        
        # 创建监控器
        self.monitor = ExchangeMonitor(self.config_manager)
        
        # 创建切换器
        self.switcher = ExchangeSwitcher(self.config_manager, self.monitor)
        
        # 设置健康状态
        self.monitor.health_status["binance"] = ExchangeHealthStatus.HEALTHY
        self.monitor.health_status["gateio"] = ExchangeHealthStatus.HEALTHY
        
        # 设置较短的冷却时间用于测试
        self.switcher.switch_cooldown = 1
    
    def teardown_method(self):
        """清理测试环境"""
        self.temp_config.close()
        os.unlink(self.temp_config.name)
    
    @pytest.mark.asyncio
    async def test_switch_to_best_exchange(self):
        """测试切换到最优交易所"""
        # 设置不同的优先级
        self.switcher.set_exchange_priority("binance", 100)
        self.switcher.set_exchange_priority("gateio", 50)
        
        # 测试切换
        best_exchange = await self.switcher.switch_to_best_exchange("BTCUSDT")
        
        # 验证选择了高优先级的交易所
        assert best_exchange == "binance"
    
    @pytest.mark.asyncio
    async def test_switch_with_current_exchange(self):
        """测试带当前交易所的切换"""
        # 设置不同的健康状态
        self.monitor.health_status["binance"] = ExchangeHealthStatus.HEALTHY
        self.monitor.health_status["gateio"] = ExchangeHealthStatus.DEGRADED
        
        # 当前交易所健康，应该保持不变
        best_exchange = await self.switcher.switch_to_best_exchange("BTCUSDT", "binance")
        assert best_exchange == "binance"
        
        # 当前交易所不健康，应该切换
        best_exchange = await self.switcher.switch_to_best_exchange("BTCUSDT", "gateio")
        assert best_exchange == "binance"
    
    @pytest.mark.asyncio
    async def test_switch_cooldown(self):
        """测试切换冷却"""
        # 设置优先级
        self.switcher.set_exchange_priority("binance", 100)
        self.switcher.set_exchange_priority("gateio", 50)
        
        # 第一次切换
        best_exchange = await self.switcher.switch_to_best_exchange("BTCUSDT", "gateio")
        assert best_exchange == "binance"
        
        # 立即再次切换，应该由于冷却时间而保持原交易所
        best_exchange = await self.switcher.switch_to_best_exchange("BTCUSDT", "binance")
        assert best_exchange == "binance"  # 保持不变
    
    def test_exchange_priority_management(self):
        """测试交易所优先级管理"""
        # 设置优先级
        self.switcher.set_exchange_priority("binance", 100)
        self.switcher.set_exchange_priority("gateio", 50)
        
        # 验证优先级设置
        assert self.switcher.exchange_priorities["binance"] == 100
        assert self.switcher.exchange_priorities["gateio"] == 50
        
        # 获取切换统计
        stats = self.switcher.get_switch_stats()
        assert stats["exchange_priorities"]["binance"] == 100
        assert stats["auto_switch_enabled"] is True
    
    def test_auto_switch_control(self):
        """测试自动切换控制"""
        # 禁用自动切换
        self.switcher.disable_auto_switch()
        assert self.switcher.auto_switch_enabled is False
        
        # 启用自动切换
        self.switcher.enable_auto_switch()
        assert self.switcher.auto_switch_enabled is True
    
    def test_load_balancing_control(self):
        """测试负载均衡控制"""
        # 禁用负载均衡
        self.switcher.disable_load_balancing()
        assert self.switcher.load_balancing_enabled is False
        
        # 启用负载均衡
        self.switcher.enable_load_balancing()
        assert self.switcher.load_balancing_enabled is True

class TestExchangeMonitoringService:
    """交易所监控服务测试"""
    
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
        
        # 创建监控服务
        self.service = ExchangeMonitoringService(self.config_manager)
    
    def teardown_method(self):
        """清理测试环境"""
        if self.service.is_running:
            asyncio.run(self.service.stop())
        self.temp_config.close()
        os.unlink(self.temp_config.name)
    
    @pytest.mark.asyncio
    async def test_service_start_stop(self):
        """测试服务启动和停止"""
        # 启动服务
        await self.service.start()
        assert self.service.is_running is True
        assert self.service.monitor.is_monitoring is True
        
        # 等待一下
        await asyncio.sleep(0.1)
        
        # 停止服务
        await self.service.stop()
        assert self.service.is_running is False
        assert self.service.monitor.is_monitoring is False
    
    @pytest.mark.asyncio
    async def test_get_best_exchange(self):
        """测试获取最优交易所"""
        # 设置健康状态
        self.service.monitor.health_status["binance"] = ExchangeHealthStatus.HEALTHY
        self.service.monitor.health_status["gateio"] = ExchangeHealthStatus.HEALTHY
        
        # 设置优先级
        self.service.switcher.set_exchange_priority("binance", 100)
        self.service.switcher.set_exchange_priority("gateio", 50)
        
        # 获取最优交易所
        best_exchange = await self.service.get_best_exchange("BTCUSDT")
        assert best_exchange == "binance"
    
    def test_health_summary(self):
        """测试健康状态摘要"""
        # 设置健康状态
        self.service.monitor.health_status["binance"] = ExchangeHealthStatus.HEALTHY
        self.service.monitor.health_status["gateio"] = ExchangeHealthStatus.DEGRADED
        
        # 添加一些告警
        alert = Alert(
            id="summary_test",
            exchange_name="gateio",
            level=AlertLevel.WARNING,
            title="摘要测试",
            message="测试健康状态摘要"
        )
        self.service.monitor.alerts.append(alert)
        
        # 获取健康状态摘要
        summary = self.service.get_health_summary()
        
        # 验证摘要内容
        assert summary["total_exchanges"] == 2
        assert summary["healthy_exchanges"] == 1
        assert summary["degraded_exchanges"] == 1
        assert summary["unhealthy_exchanges"] == 0
        assert summary["active_alerts"] == 1
        assert summary["warning_alerts"] == 1
        assert summary["critical_alerts"] == 0
        assert summary["monitoring_enabled"] is False  # 服务未启动
        assert summary["auto_switch_enabled"] is True

@pytest.mark.asyncio
async def test_exchange_monitoring_integration():
    """交易所监控集成测试"""
    """测试交易所监控和切换的完整流程"""
    
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
"""
        f.write(config_content)
        f.flush()
        
        try:
            # 创建配置管理器
            config_manager = ExchangeConfigManager(f.name)
            config = config_manager.load_config()
            
            # 创建监控服务
            service = ExchangeMonitoringService(config_manager)
            
            # 测试健康摘要
            summary = service.get_health_summary()
            assert summary["total_exchanges"] == 2
            assert summary["monitoring_enabled"] is False
            
            # 测试组件创建
            assert service.monitor is not None
            assert service.switcher is not None
            assert service.switcher.auto_switch_enabled is True
            
            # 测试优先级设置
            service.switcher.set_exchange_priority("binance", 100)
            assert service.switcher.exchange_priorities["binance"] == 100
            
            # 测试切换控制
            service.switcher.disable_auto_switch()
            assert service.switcher.auto_switch_enabled is False
            
            service.switcher.enable_auto_switch()
            assert service.switcher.auto_switch_enabled is True
            
        finally:
            os.unlink(f.name)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])