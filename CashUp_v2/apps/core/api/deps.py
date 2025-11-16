from typing import AsyncGenerator, Any
import os
import yaml
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.adapters.exchanges.base import ExchangeManager
from utils.crypto import decrypt_str
from database.connection import get_db, get_database
from config.settings import settings

_exchange_manager: ExchangeManager | None = None

def _load_exchanges_config() -> dict:
    path = os.path.join(os.getcwd(), "configs", "exchanges.yaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def reset_exchange_manager():
    global _exchange_manager
    _exchange_manager = None

async def _build_manager_from_db(session: AsyncSession) -> ExchangeManager:
    mgr = ExchangeManager()
    cfg = _load_exchanges_config()
    res = await session.execute(text("SELECT exchange, name, key_data, secret_data, passphrase, is_active FROM api_keys"))
    rows = res.fetchall()
    db_map = {}
    for r in rows:
        db_map.setdefault(r.exchange, []).append(r)
    for ex_name, conf in cfg.items():
        if ex_name in ("common", "risk_control", "monitoring"):
            continue
        base_conf = conf if isinstance(conf, dict) else {}
        # 环境变量展开
        for k, v in list(base_conf.items()):
            if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
                env_key = v[2:-1]
                base_conf[k] = os.getenv(env_key, "")
        # DB 覆盖
        db_rows = db_map.get(ex_name, [])
        active_row = next((r for r in db_rows if r.is_active), None)
        if active_row:
            try:
                dec_key = decrypt_str(active_row.key_data) if active_row.key_data else base_conf.get("api_key", "")
            except Exception:
                dec_key = active_row.key_data or base_conf.get("api_key", "")
            try:
                dec_sec = decrypt_str(active_row.secret_data) if active_row.secret_data else base_conf.get("api_secret", "")
            except Exception:
                dec_sec = active_row.secret_data or base_conf.get("api_secret", "")
            base_conf["api_key"] = dec_key
            base_conf["api_secret"] = dec_sec
            base_conf["enabled"] = True
        enabled = bool(base_conf.get("enabled", False))
        if enabled:
            base_conf["name"] = base_conf.get("name", ex_name)
            base_conf["type"] = base_conf.get("type", ex_name)
            mgr.add_exchange(ex_name, base_conf)
    return mgr

def get_exchange_manager() -> ExchangeManager:
    global _exchange_manager
    return _exchange_manager  # 外部请使用 get_exchanges 以确保初始化

async def get_exchanges() -> AsyncGenerator[ExchangeManager, None]:
    """获取交易所管理器（基于配置，免DB依赖）"""
    global _exchange_manager
    if _exchange_manager is None:
        cfg = _load_exchanges_config()
        mgr = ExchangeManager()
        for ex_name, conf in cfg.items():
            if ex_name in ("common", "risk_control", "monitoring"):
                continue
            base_conf = conf if isinstance(conf, dict) else {}
            # 环境变量展开
            for k, v in list(base_conf.items()):
                if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
                    env_key = v[2:-1]
                    base_conf[k] = os.getenv(env_key, "")
            enabled = bool(base_conf.get("enabled", False))
            if enabled:
                base_conf["name"] = base_conf.get("name", ex_name)
                base_conf["type"] = base_conf.get("type", ex_name)
                mgr.add_exchange(ex_name, base_conf)
        _exchange_manager = mgr
    yield _exchange_manager

#
# 认证相关依赖
#
security = HTTPBearer(auto_error=False)

class SimpleUser:
    """简易用户模型，兼容前端所需的最小字段"""
    def __init__(self, id: str = "dev", username: str = "developer", role: str = "admin"):
        self.id = id
        self.username = username
        self.role = role

async def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> Any:
    """获取当前用户（支持禁用认证时返回默认用户）"""
    if not settings.ENABLE_AUTH:
        return SimpleUser()
    # TODO: 这里可以接入真实的JWT/Cookie校验逻辑
    # 暂时在未实现完整认证时返回默认用户，避免阻塞原型开发
    if credentials is None or not (credentials.scheme and credentials.credentials):
        return SimpleUser()
    token = credentials.credentials
    # 仅占位解析逻辑：实际应验证签名并提取用户ID/角色
    return SimpleUser(id="token_user", username="token_user", role="admin")