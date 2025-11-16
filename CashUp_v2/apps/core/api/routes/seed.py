from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import os
import yaml

from database.connection import get_db

router = APIRouter()

@router.post("/api/v1/seed/configs")
async def seed_configs(db: AsyncSession = Depends(get_db)):
    await db.execute(text(
        """
        CREATE TABLE IF NOT EXISTS api_keys (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            exchange VARCHAR(50) NOT NULL,
            name VARCHAR(100) NOT NULL,
            key_data TEXT NOT NULL,
            secret_data TEXT NOT NULL,
            passphrase TEXT,
            is_active BOOLEAN DEFAULT true,
            permissions JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    ))
    # exchanges.yaml -> api_keys
    path = os.path.join(os.getcwd(), "configs", "exchanges.yaml")
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
    except Exception:
        cfg = {}
    count = 0
    for name, conf in cfg.items():
        if name in ("common", "risk_control", "monitoring"):
            continue
        if not isinstance(conf, dict):
            continue
        api_key = conf.get("api_key", "")
        api_secret = conf.get("api_secret", "")
        if isinstance(api_key, str) and api_key.startswith("${") and api_key.endswith("}"):
            api_key = os.getenv(api_key[2:-1], "")
        if isinstance(api_secret, str) and api_secret.startswith("${") and api_secret.endswith("}"):
            api_secret = os.getenv(api_secret[2:-1], "")
        enabled = bool(conf.get("enabled", False))
        if api_key or api_secret:
            await db.execute(text("INSERT INTO public.api_keys (user_id, exchange, name, key_data, secret_data, is_active) VALUES (NULL, :ex, 'default', :key, :sec, :enabled) ON CONFLICT DO NOTHING"), {"ex": name, "key": api_key, "sec": api_secret, "enabled": enabled})
            count += 1
    return {"code": 0, "message": "seeded", "data": {"keys": count}}
    
@router.post("/api/v1/seed/system_configs")
async def seed_system_configs(db: AsyncSession = Depends(get_db)):
    await db.execute(text(
        """
        CREATE TABLE IF NOT EXISTS system_configs (
            key VARCHAR(255) PRIMARY KEY,
            value TEXT NOT NULL,
            is_system BOOLEAN DEFAULT false,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    ))
    defaults = [
        ("trading.sync.interval", '"60"'),
        ("notification.default_channels", '["telegram","webhook"]'),
        ("risk.default", '{"max_position_size":1,"stop_loss":0.02,"take_profit":0.03}'),
        ("rss.fetch.interval", '"300"'),
        ("rss.analyze.interval", '"600"'),
        ("rss.correlation.interval", '"900"'),
    ]
    from sqlalchemy import bindparam
    from sqlalchemy.types import JSON
    stmt = text("INSERT INTO system_configs (config_key, config_value) VALUES (:k, :v) ON CONFLICT (config_key) DO NOTHING").bindparams(bindparam("v", type_=JSON))
    for k, v in defaults:
        # v 是 JSON 文本，转为对象
        import json as _json
        try:
            obj = _json.loads(v)
        except Exception:
            obj = v
        await db.execute(stmt, {"k": k, "v": obj})
    await db.commit()
    return {"code": 0, "message": "seeded"}