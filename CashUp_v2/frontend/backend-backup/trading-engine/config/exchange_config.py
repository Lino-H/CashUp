"""
交易所配置管理模块
"""

import os
import yaml
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class ExchangeConfig:
    """单个交易所配置"""
    type: str
    name: str
    sandbox: bool = False
    rate_limit: int = 10
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    passphrase: Optional[str] = None
    base_url: str = ""
    stream_url: str = ""
    testnet_base_url: str = ""
    testnet_stream_url: str = ""
    symbols: List[str] = field(default_factory=list)
    enabled: bool = True
    timeout: int = 30
    retry_count: int = 3
    retry_interval: int = 1

@dataclass
class CommonConfig:
    """通用配置"""
    timeout: int = 30
    retry_count: int = 3
    retry_interval: int = 1
    cache_ttl: int = 60
    log_level: str = "INFO"
    enable_websocket: bool = True
    heartbeat_interval: int = 30

@dataclass
class RiskControlConfig:
    """风险控制配置"""
    max_order_amount: float = 10000
    max_position_ratio: float = 0.8
    min_order_amount: float = 10
    max_daily_loss: float = 1000
    max_daily_trades: int = 100

@dataclass
class MonitoringConfig:
    """监控配置"""
    enabled: bool = True
    interval: int = 60
    alert_threshold: Dict[str, Any] = field(default_factory=dict)
    notification_channels: List[Dict[str, str]] = field(default_factory=list)

@dataclass
class ExchangeGlobalConfig:
    """全局交易所配置"""
    exchanges: Dict[str, ExchangeConfig] = field(default_factory=dict)
    common: CommonConfig = field(default_factory=CommonConfig)
    risk_control: RiskControlConfig = field(default_factory=RiskControlConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)

class ExchangeConfigManager:
    """交易所配置管理器"""
    
    def __init__(self, config_path: str = "configs/exchanges.yaml"):
        self.config_path = Path(config_path)
        self.config: Optional[ExchangeGlobalConfig] = None
        self.load_config()
    
    def load_config(self) -> ExchangeGlobalConfig:
        """加载配置文件"""
        try:
            if not self.config_path.exists():
                logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
                return self._create_default_config()
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # 解析环境变量
            config_data = self._resolve_env_vars(config_data)
            
            # 转换为配置对象
            self.config = self._parse_config(config_data)
            logger.info(f"成功加载配置文件: {self.config_path}")
            
            return self.config
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return self._create_default_config()
    
    def _resolve_env_vars(self, data: Any) -> Any:
        """解析环境变量"""
        if isinstance(data, dict):
            return {k: self._resolve_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._resolve_env_vars(item) for item in data]
        elif isinstance(data, str) and data.startswith("${") and data.endswith("}"):
            env_var = data[2:-1]
            return os.getenv(env_var, "")
        else:
            return data
    
    def _parse_config(self, data: Dict[str, Any]) -> ExchangeGlobalConfig:
        """解析配置数据"""
        config = ExchangeGlobalConfig()
        
        # 解析交易所配置
        for name, exchange_data in data.items():
            if name in ["common", "risk_control", "monitoring"]:
                continue
            
            if exchange_data.get("enabled", True):
                exchange_config = ExchangeConfig(**exchange_data)
                config.exchanges[name] = exchange_config
                logger.info(f"添加交易所配置: {name} ({exchange_config.type})")
        
        # 解析通用配置
        if "common" in data:
            config.common = CommonConfig(**data["common"])
        
        # 解析风险控制配置
        if "risk_control" in data:
            config.risk_control = RiskControlConfig(**data["risk_control"])
        
        # 解析监控配置
        if "monitoring" in data:
            config.monitoring = MonitoringConfig(**data["monitoring"])
        
        return config
    
    def _create_default_config(self) -> ExchangeGlobalConfig:
        """创建默认配置"""
        config = ExchangeGlobalConfig()
        
        # 添加Binance默认配置
        config.exchanges["binance"] = ExchangeConfig(
            type="binance",
            name="Binance",
            base_url="https://api.binance.com",
            stream_url="wss://stream.binance.com:9443",
            testnet_base_url="https://testnet.binance.vision",
            testnet_stream_url="wss://testnet.binance.vision",
            symbols=["BTCUSDT", "ETHUSDT"],
            enabled=False
        )
        
        # 添加Gate.io默认配置
        config.exchanges["gateio"] = ExchangeConfig(
            type="gateio",
            name="Gate.io",
            base_url="https://api.gateio.ws",
            stream_url="wss://ws.gate.io",
            testnet_base_url="https://fx-api-testnet.gateio.ws",
            testnet_stream_url="wss://fx-ws-testnet.gateio.ws",
            symbols=["BTC_USDT", "ETH_USDT"],
            enabled=False
        )
        
        self.config = config
        return config
    
    def get_exchange_config(self, name: str) -> Optional[ExchangeConfig]:
        """获取指定交易所配置"""
        if not self.config:
            return None
        
        return self.config.exchanges.get(name)
    
    def get_enabled_exchanges(self) -> Dict[str, ExchangeConfig]:
        """获取所有启用的交易所配置"""
        if not self.config:
            return {}
        
        return {name: config for name, config in self.config.exchanges.items() 
                if config.enabled}
    
    def get_exchange_names(self) -> List[str]:
        """获取所有交易所名称"""
        if not self.config:
            return []
        
        return list(self.config.exchanges.keys())
    
    def get_enabled_exchange_names(self) -> List[str]:
        """获取所有启用的交易所名称"""
        if not self.config:
            return []
        
        return [name for name, config in self.config.exchanges.items() 
                if config.enabled]
    
    def is_exchange_enabled(self, name: str) -> bool:
        """检查交易所是否启用"""
        config = self.get_exchange_config(name)
        return config and config.enabled
    
    def enable_exchange(self, name: str) -> bool:
        """启用交易所"""
        if not self.config:
            return False
        
        if name in self.config.exchanges:
            self.config.exchanges[name].enabled = True
            logger.info(f"已启用交易所: {name}")
            return True
        
        return False
    
    def disable_exchange(self, name: str) -> bool:
        """禁用交易所"""
        if not self.config:
            return False
        
        if name in self.config.exchanges:
            self.config.exchanges[name].enabled = False
            logger.info(f"已禁用交易所: {name}")
            return True
        
        return False
    
    def update_exchange_config(self, name: str, updates: Dict[str, Any]) -> bool:
        """更新交易所配置"""
        if not self.config:
            return False
        
        if name not in self.config.exchanges:
            return False
        
        config = self.config.exchanges[name]
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        logger.info(f"已更新交易所配置: {name}")
        return True
    
    def add_exchange_config(self, name: str, config: ExchangeConfig) -> bool:
        """添加交易所配置"""
        if not self.config:
            return False
        
        self.config.exchanges[name] = config
        logger.info(f"已添加交易所配置: {name} ({config.type})")
        return True
    
    def remove_exchange_config(self, name: str) -> bool:
        """移除交易所配置"""
        if not self.config:
            return False
        
        if name in self.config.exchanges:
            del self.config.exchanges[name]
            logger.info(f"已移除交易所配置: {name}")
            return True
        
        return False
    
    def save_config(self) -> bool:
        """保存配置到文件"""
        if not self.config:
            return False
        
        try:
            # 转换为字典格式
            config_data = {}
            
            # 保存交易所配置
            for name, config in self.config.exchanges.items():
                config_data[name] = {
                    "type": config.type,
                    "name": config.name,
                    "sandbox": config.sandbox,
                    "rate_limit": config.rate_limit,
                    "api_key": config.api_key,
                    "api_secret": config.api_secret,
                    "passphrase": config.passphrase,
                    "base_url": config.base_url,
                    "stream_url": config.stream_url,
                    "testnet_base_url": config.testnet_base_url,
                    "testnet_stream_url": config.testnet_stream_url,
                    "symbols": config.symbols,
                    "enabled": config.enabled
                }
            
            # 保存通用配置
            config_data["common"] = {
                "timeout": self.config.common.timeout,
                "retry_count": self.config.common.retry_count,
                "retry_interval": self.config.common.retry_interval,
                "cache_ttl": self.config.common.cache_ttl,
                "log_level": self.config.common.log_level,
                "enable_websocket": self.config.common.enable_websocket,
                "heartbeat_interval": self.config.common.heartbeat_interval
            }
            
            # 保存风险控制配置
            config_data["risk_control"] = {
                "max_order_amount": self.config.risk_control.max_order_amount,
                "max_position_ratio": self.config.risk_control.max_position_ratio,
                "min_order_amount": self.config.risk_control.min_order_amount,
                "max_daily_loss": self.config.risk_control.max_daily_loss,
                "max_daily_trades": self.config.risk_control.max_daily_trades
            }
            
            # 保存监控配置
            config_data["monitoring"] = {
                "enabled": self.config.monitoring.enabled,
                "interval": self.config.monitoring.interval,
                "alert_threshold": self.config.monitoring.alert_threshold,
                "notification_channels": self.config.monitoring.notification_channels
            }
            
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"配置已保存到: {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False
    
    def validate_config(self) -> List[str]:
        """验证配置有效性"""
        errors = []
        
        if not self.config:
            errors.append("配置未加载")
            return errors
        
        # 验证交易所配置
        for name, config in self.config.exchanges.items():
            if not config.type:
                errors.append(f"{name}: 交易所类型不能为空")
            
            if not config.name:
                errors.append(f"{name}: 交易所名称不能为空")
            
            if config.enabled:
                if not config.api_key:
                    errors.append(f"{name}: API密钥不能为空")
                
                if not config.api_secret:
                    errors.append(f"{name}: API密钥不能为空")
                
                if not config.base_url:
                    errors.append(f"{name}: 基础URL不能为空")
                
                if not config.symbols:
                    errors.append(f"{name}: 交易对列表不能为空")
        
        return errors
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        if not self.config:
            return {}
        
        summary = {
            "total_exchanges": len(self.config.exchanges),
            "enabled_exchanges": len(self.get_enabled_exchanges()),
            "exchange_types": list(set(config.type for config in self.config.exchanges.values())),
            "common_config": {
                "timeout": self.config.common.timeout,
                "retry_count": self.config.common.retry_count,
                "log_level": self.config.common.log_level
            },
            "risk_control": {
                "max_order_amount": self.config.risk_control.max_order_amount,
                "max_position_ratio": self.config.risk_control.max_position_ratio
            },
            "monitoring": {
                "enabled": self.config.monitoring.enabled,
                "interval": self.config.monitoring.interval
            }
        }
        
        return summary