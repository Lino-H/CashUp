"""
交易所监控和切换模块
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import time
import json

from .config_driven_manager import ConfigDrivenExchangeManager
from .multi_exchange_manager import MultiExchangeManager
from ..exchanges.base import ExchangeAdapter

logger = logging.getLogger(__name__)

class ExchangeHealthStatus(Enum):
    """交易所健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"
    UNKNOWN = "unknown"

class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ExchangeMetrics:
    """交易所指标"""
    exchange_name: str
    response_time: float = 0.0
    success_rate: float = 1.0
    error_count: int = 0
    total_requests: int = 0
    last_check: Optional[datetime] = None
    uptime: float = 100.0
    connection_status: bool = True
    
@dataclass
class HealthCheckResult:
    """健康检查结果"""
    exchange_name: str
    status: ExchangeHealthStatus
    metrics: ExchangeMetrics
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class Alert:
    """告警信息"""
    id: str
    exchange_name: str
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class ExchangeMonitor:
    """交易所监控器"""
    
    def __init__(self, config_manager: ConfigDrivenExchangeManager, 
                 multi_manager: Optional[MultiExchangeManager] = None):
        self.config_manager = config_manager
        self.multi_manager = multi_manager
        
        # 监控配置
        self.check_interval = 60  # 检查间隔（秒）
        self.response_time_threshold = 5.0  # 响应时间阈值（秒）
        self.success_rate_threshold = 0.95  # 成功率阈值
        self.max_error_count = 10  # 最大错误次数
        
        # 监控数据
        self.metrics: Dict[str, ExchangeMetrics] = {}
        self.health_status: Dict[str, ExchangeHealthStatus] = {}
        self.alerts: List[Alert] = []
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        
        # 监控任务
        self.monitor_task: Optional[asyncio.Task] = None
        self.is_monitoring = False
        
        # 告警计数器
        self.alert_counters: Dict[str, Dict[str, int]] = {}
        
    async def start_monitoring(self):
        """开始监控"""
        if self.is_monitoring:
            logger.warning("监控已经在运行中")
            return
        
        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("交易所监控已启动")
    
    async def stop_monitoring(self):
        """停止监控"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("交易所监控已停止")
    
    async def _monitor_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                await self._check_all_exchanges()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控循环出错: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_all_exchanges(self):
        """检查所有交易所"""
        exchanges = self.config_manager.get_enabled_exchanges()
        
        for exchange_name in exchanges:
            try:
                await self._check_exchange_health(exchange_name)
            except Exception as e:
                logger.error(f"检查交易所健康状态失败 {exchange_name}: {e}")
    
    async def _check_exchange_health(self, exchange_name: str) -> HealthCheckResult:
        """检查单个交易所健康状态"""
        start_time = time.time()
        
        # 获取交易所适配器
        adapter = self.config_manager.get_exchange_adapter(exchange_name)
        if not adapter:
            result = HealthCheckResult(
                exchange_name=exchange_name,
                status=ExchangeHealthStatus.UNKNOWN,
                metrics=ExchangeMetrics(exchange_name=exchange_name),
                issues=["交易所适配器不存在"],
                recommendations=["检查交易所配置"]
            )
            self.health_status[exchange_name] = result.status
            return result
        
        # 获取或创建指标
        if exchange_name not in self.metrics:
            self.metrics[exchange_name] = ExchangeMetrics(exchange_name=exchange_name)
        
        metrics = self.metrics[exchange_name]
        
        # 测试连接
        connection_ok = False
        response_time = 0.0
        issues = []
        recommendations = []
        
        try:
            connection_start = time.time()
            connection_ok = await adapter.test_connection()
            response_time = time.time() - connection_start
            
            if connection_ok:
                # 测试基本API调用
                try:
                    await adapter.get_server_time()
                except Exception as e:
                    connection_ok = False
                    issues.append(f"API调用失败: {str(e)}")
                    recommendations.append("检查API密钥和网络连接")
            
        except Exception as e:
            connection_ok = False
            issues.append(f"连接测试失败: {str(e)}")
            recommendations.append("检查交易所服务状态")
        
        # 更新指标
        metrics.response_time = response_time
        metrics.connection_status = connection_ok
        metrics.last_check = datetime.now()
        
        if not connection_ok:
            metrics.error_count += 1
        
        metrics.total_requests += 1
        metrics.success_rate = (metrics.total_requests - metrics.error_count) / metrics.total_requests
        
        # 计算健康状态
        status = self._calculate_health_status(metrics, issues)
        
        # 生成告警
        await self._generate_alerts(exchange_name, status, metrics, issues)
        
        # 创建健康检查结果
        result = HealthCheckResult(
            exchange_name=exchange_name,
            status=status,
            metrics=metrics,
            issues=issues,
            recommendations=recommendations
        )
        
        self.health_status[exchange_name] = status
        
        # 记录健康检查结果
        self._log_health_check(result)
        
        return result
    
    def _calculate_health_status(self, metrics: ExchangeMetrics, issues: List[str]) -> ExchangeHealthStatus:
        """计算健康状态"""
        if not metrics.connection_status:
            return ExchangeHealthStatus.OFFLINE
        
        if metrics.error_count > self.max_error_count:
            return ExchangeHealthStatus.UNHEALTHY
        
        if metrics.success_rate < self.success_rate_threshold:
            return ExchangeHealthStatus.UNHEALTHY
        
        if metrics.response_time > self.response_time_threshold:
            return ExchangeHealthStatus.DEGRADED
        
        if issues:
            return ExchangeHealthStatus.DEGRADED
        
        return ExchangeHealthStatus.HEALTHY
    
    async def _generate_alerts(self, exchange_name: str, status: ExchangeHealthStatus, 
                             metrics: ExchangeMetrics, issues: List[str]):
        """生成告警"""
        alerts_to_create = []
        
        # 根据状态生成告警
        if status == ExchangeHealthStatus.OFFLINE:
            alerts_to_create.append(Alert(
                id=f"{exchange_name}_offline_{int(time.time())}",
                exchange_name=exchange_name,
                level=AlertLevel.CRITICAL,
                title="交易所离线",
                message=f"交易所 {exchange_name} 离线，无法连接",
                metadata={"status": status.value}
            ))
        
        elif status == ExchangeHealthStatus.UNHEALTHY:
            alerts_to_create.append(Alert(
                id=f"{exchange_name}_unhealthy_{int(time.time())}",
                exchange_name=exchange_name,
                level=AlertLevel.ERROR,
                title="交易所不健康",
                message=f"交易所 {exchange_name} 状态不健康: {', '.join(issues)}",
                metadata={"status": status.value, "issues": issues}
            ))
        
        elif status == ExchangeHealthStatus.DEGRADED:
            alerts_to_create.append(Alert(
                id=f"{exchange_name}_degraded_{int(time.time())}",
                exchange_name=exchange_name,
                level=AlertLevel.WARNING,
                title="交易所性能下降",
                message=f"交易所 {exchange_name} 性能下降，响应时间: {metrics.response_time:.2f}s",
                metadata={"status": status.value, "response_time": metrics.response_time}
            ))
        
        # 检查错误率
        if metrics.success_rate < self.success_rate_threshold and metrics.total_requests > 10:
            alerts_to_create.append(Alert(
                id=f"{exchange_name}_high_error_rate_{int(time.time())}",
                exchange_name=exchange_name,
                level=AlertLevel.WARNING,
                title="交易所错误率过高",
                message=f"交易所 {exchange_name} 错误率过高: {(1-metrics.success_rate)*100:.1f}%",
                metadata={"success_rate": metrics.success_rate}
            ))
        
        # 限制告警频率
        for alert in alerts_to_create:
            if self._should_send_alert(alert):
                self.alerts.append(alert)
                await self._notify_alert(alert)
    
    def _should_send_alert(self, alert: Alert) -> bool:
        """检查是否应该发送告警"""
        key = f"{alert.exchange_name}_{alert.level.value}"
        
        if key not in self.alert_counters:
            self.alert_counters[key] = {"count": 0, "last_sent": None}
        
        counter = self.alert_counters[key]
        
        # 限制告警频率（每5分钟最多发送一次相同级别的告警）
        if counter["last_sent"] and (datetime.now() - counter["last_sent"]).seconds < 300:
            return False
        
        counter["count"] += 1
        counter["last_sent"] = datetime.now()
        
        return True
    
    async def _notify_alert(self, alert: Alert):
        """通知告警"""
        logger.warning(f"交易所告警: [{alert.level.value.upper()}] {alert.exchange_name} - {alert.title}")
        
        # 调用告警回调
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                logger.error(f"告警回调失败: {e}")
    
    def _log_health_check(self, result: HealthCheckResult):
        """记录健康检查结果"""
        logger.info(f"健康检查 {result.exchange_name}: {result.status.value} - "
                   f"响应时间: {result.metrics.response_time:.2f}s, "
                   f"成功率: {result.metrics.success_rate:.2%}")
    
    def get_health_status(self, exchange_name: Optional[str] = None) -> Dict[str, Any]:
        """获取健康状态"""
        if exchange_name:
            return {
                "exchange_name": exchange_name,
                "status": self.health_status.get(exchange_name, ExchangeHealthStatus.UNKNOWN).value,
                "metrics": self.metrics.get(exchange_name).__dict__ if exchange_name in self.metrics else None,
                "last_check": self.metrics[exchange_name].last_check.isoformat() if exchange_name in self.metrics and self.metrics[exchange_name].last_check else None
            }
        else:
            return {
                name: {
                    "status": status.value,
                    "metrics": self.metrics[name].__dict__ if name in self.metrics else None,
                    "last_check": self.metrics[name].last_check.isoformat() if name in self.metrics and self.metrics[name].last_check else None
                }
                for name, status in self.health_status.items()
            }
    
    def get_alerts(self, exchange_name: Optional[str] = None, 
                  level: Optional[AlertLevel] = None, 
                  resolved: Optional[bool] = None) -> List[Alert]:
        """获取告警列表"""
        alerts = self.alerts
        
        if exchange_name:
            alerts = [alert for alert in alerts if alert.exchange_name == exchange_name]
        
        if level:
            alerts = [alert for alert in alerts if alert.level == level]
        
        if resolved is not None:
            alerts = [alert for alert in alerts if alert.resolved == resolved]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                logger.info(f"告警已解决: {alert.title}")
                return True
        
        return False
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """添加告警回调"""
        self.alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable[[Alert], None]):
        """移除告警回调"""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)

class ExchangeSwitcher:
    """交易所切换器"""
    
    def __init__(self, config_manager: ConfigDrivenExchangeManager, 
                 monitor: ExchangeMonitor):
        self.config_manager = config_manager
        self.monitor = monitor
        
        # 切换策略
        self.auto_switch_enabled = True
        self.switch_cooldown = 300  # 切换冷却时间（秒）
        self.last_switch_time: Dict[str, datetime] = {}
        
        # 优先级配置
        self.exchange_priorities: Dict[str, int] = {}
        self.load_balancing_enabled = True
        
    async def switch_to_best_exchange(self, symbol: str, 
                                    current_exchange: Optional[str] = None) -> Optional[str]:
        """切换到最优交易所"""
        if not self.auto_switch_enabled:
            return None
        
        # 获取所有启用的交易所
        exchanges = self.config_manager.get_enabled_exchange_names()
        
        # 过滤掉不健康的交易所
        healthy_exchanges = []
        for exchange_name in exchanges:
            status = self.monitor.health_status.get(exchange_name)
            if status in [ExchangeHealthStatus.HEALTHY, ExchangeHealthStatus.DEGRADED]:
                healthy_exchanges.append(exchange_name)
        
        if not healthy_exchanges:
            logger.warning("没有健康的交易所可用")
            return None
        
        # 如果当前交易所健康且在列表中，保持不变
        if current_exchange and current_exchange in healthy_exchanges:
            return current_exchange
        
        # 选择最优交易所
        best_exchange = await self._select_best_exchange(healthy_exchanges, symbol)
        
        # 检查切换冷却时间
        if current_exchange and best_exchange != current_exchange:
            if not self._can_switch(current_exchange, best_exchange):
                logger.info(f"切换冷却中，保持当前交易所: {current_exchange}")
                return current_exchange
        
        # 执行切换
        if best_exchange != current_exchange:
            await self._execute_switch(current_exchange, best_exchange, symbol)
            self.last_switch_time[best_exchange] = datetime.now()
            logger.info(f"已切换到交易所: {best_exchange}")
        
        return best_exchange
    
    async def _select_best_exchange(self, exchanges: List[str], symbol: str) -> str:
        """选择最优交易所"""
        if not self.load_balancing_enabled:
            # 按优先级选择
            for exchange_name in exchanges:
                priority = self.exchange_priorities.get(exchange_name, 0)
                if priority > 0:
                    return exchange_name
        
        # 如果没有优先级配置，使用默认策略
        best_exchange = exchanges[0]
        best_score = -1
        
        for exchange_name in exchanges:
            score = await self._calculate_exchange_score(exchange_name, symbol)
            
            if score > best_score:
                best_score = score
                best_exchange = exchange_name
        
        return best_exchange
    
    async def _calculate_exchange_score(self, exchange_name: str, symbol: str) -> float:
        """计算交易所评分"""
        metrics = self.monitor.metrics.get(exchange_name)
        if not metrics:
            return 0.0
        
        score = 0.0
        
        # 响应时间权重 (40%)
        response_time_score = max(0, 1 - (metrics.response_time / 10.0))  # 10秒为满分
        score += response_time_score * 0.4
        
        # 成功率权重 (40%)
        success_rate_score = metrics.success_rate
        score += success_rate_score * 0.4
        
        # 优先级权重 (20%)
        priority_score = self.exchange_priorities.get(exchange_name, 50) / 100.0
        score += priority_score * 0.2
        
        return score
    
    def _can_switch(self, from_exchange: str, to_exchange: str) -> bool:
        """检查是否可以切换"""
        # 检查切换冷却时间
        last_switch = self.last_switch_time.get(to_exchange)
        if last_switch and (datetime.now() - last_switch).seconds < self.switch_cooldown:
            return False
        
        return True
    
    async def _execute_switch(self, from_exchange: Optional[str], to_exchange: str, symbol: str):
        """执行切换"""
        logger.info(f"执行交易所切换: {from_exchange} -> {to_exchange} (symbol: {symbol})")
        
        # 这里可以添加切换前的清理工作
        # 比如取消未完成的订单、同步数据等
        
        # 记录切换事件
        switch_event = {
            "from_exchange": from_exchange,
            "to_exchange": to_exchange,
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "reason": "auto_switch"
        }
        
        logger.info(f"交易所切换事件: {json.dumps(switch_event)}")
    
    def set_exchange_priority(self, exchange_name: str, priority: int):
        """设置交易所优先级"""
        self.exchange_priorities[exchange_name] = priority
        logger.info(f"设置交易所优先级: {exchange_name} -> {priority}")
    
    def enable_auto_switch(self):
        """启用自动切换"""
        self.auto_switch_enabled = True
        logger.info("已启用自动切换")
    
    def disable_auto_switch(self):
        """禁用自动切换"""
        self.auto_switch_enabled = False
        logger.info("已禁用自动切换")
    
    def enable_load_balancing(self):
        """启用负载均衡"""
        self.load_balancing_enabled = True
        logger.info("已启用负载均衡")
    
    def disable_load_balancing(self):
        """禁用负载均衡"""
        self.load_balancing_enabled = False
        logger.info("已禁用负载均衡")
    
    def get_switch_stats(self) -> Dict[str, Any]:
        """获取切换统计"""
        return {
            "auto_switch_enabled": self.auto_switch_enabled,
            "load_balancing_enabled": self.load_balancing_enabled,
            "exchange_priorities": self.exchange_priorities,
            "last_switch_times": {
                name: time.isoformat() 
                for name, time in self.last_switch_time.items()
            },
            "switch_cooldown": self.switch_cooldown
        }

class ExchangeMonitoringService:
    """交易所监控服务"""
    
    def __init__(self, config_manager: ConfigDrivenExchangeManager,
                 multi_manager: Optional[MultiExchangeManager] = None):
        self.config_manager = config_manager
        self.multi_manager = multi_manager
        
        # 创建组件
        self.monitor = ExchangeMonitor(config_manager, multi_manager)
        self.switcher = ExchangeSwitcher(config_manager, self.monitor)
        
        # 服务状态
        self.is_running = False
        
    async def start(self):
        """启动监控服务"""
        if self.is_running:
            logger.warning("监控服务已经在运行中")
            return
        
        await self.monitor.start_monitoring()
        self.is_running = True
        logger.info("交易所监控服务已启动")
    
    async def stop(self):
        """停止监控服务"""
        if not self.is_running:
            return
        
        await self.monitor.stop_monitoring()
        self.is_running = False
        logger.info("交易所监控服务已停止")
    
    async def get_best_exchange(self, symbol: str, 
                              current_exchange: Optional[str] = None) -> Optional[str]:
        """获取最优交易所"""
        return await self.switcher.switch_to_best_exchange(symbol, current_exchange)
    
    def get_health_summary(self) -> Dict[str, Any]:
        """获取健康状态摘要"""
        health_status = self.monitor.get_health_status()
        alerts = self.monitor.get_alerts(resolved=False)
        
        summary = {
            "total_exchanges": len(health_status),
            "healthy_exchanges": len([s for s in health_status.values() if s["status"] == "healthy"]),
            "degraded_exchanges": len([s for s in health_status.values() if s["status"] == "degraded"]),
            "unhealthy_exchanges": len([s for s in health_status.values() if s["status"] in ["unhealthy", "offline"]]),
            "active_alerts": len(alerts),
            "critical_alerts": len([a for a in alerts if a.level == AlertLevel.CRITICAL]),
            "warning_alerts": len([a for a in alerts if a.level == AlertLevel.WARNING]),
            "monitoring_enabled": self.is_running,
            "auto_switch_enabled": self.switcher.auto_switch_enabled
        }
        
        return summary