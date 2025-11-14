from typing import AsyncGenerator
import os
import yaml

from app.adapters.exchanges.base import ExchangeManager

_exchange_manager: ExchangeManager | None = None

def _load_exchanges_config() -> dict:
    path = os.path.join(os.getcwd(), "configs", "exchanges.yaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_exchange_manager() -> ExchangeManager:
    global _exchange_manager
    if _exchange_manager is None:
        cfg = _load_exchanges_config()
        mgr = ExchangeManager()
        for name, conf in cfg.items():
            if name in ("common", "risk_control", "monitoring"):
                continue
            if isinstance(conf, dict) and conf.get("enabled", False):
                # 环境变量展开（如 ${BINANCE_API_KEY}）
                for k, v in list(conf.items()):
                    if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
                        env_key = v[2:-1]
                        conf[k] = os.getenv(env_key, "")
                conf["name"] = conf.get("name", name)
                conf["type"] = conf.get("type", name)
                mgr.add_exchange(name, conf)
        _exchange_manager = mgr
    return _exchange_manager

async def get_exchanges() -> AsyncGenerator[ExchangeManager, None]:
    yield get_exchange_manager()