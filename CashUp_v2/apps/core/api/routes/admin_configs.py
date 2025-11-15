from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, bindparam
from sqlalchemy.types import JSON
import json
from typing import Optional

from database.connection import get_db

router = APIRouter()

@router.get("/api/v1/configs/{key}")
async def get_config_item(key: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(text("SELECT config_key, config_value FROM system_configs WHERE config_key=:key"), {"key": key})
    row = res.first()
    if not row:
        return {"code": 404, "message": "not found"}
    return {"code": 0, "message": "success", "data": {"key": row.config_key, "value": row.config_value}}

def _apply_advice(key: str) -> dict:
    if key.startswith("trading.sync."):
        return {"type": "reload", "modules": ["celery_beat"]}
    if key == "notification.default_channels":
        return {"type": "immediate"}
    if key.startswith("risk."):
        return {"type": "immediate"}
    return {"type": "immediate"}

from fastapi import Body

@router.put("/api/v1/configs/{key}")
async def set_config_item(key: str, payload: dict = Body(...), db: AsyncSession = Depends(get_db)):
    raw = payload.get("value")
    try:
        value_obj = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        value_obj = raw
    stmt = text("INSERT INTO system_configs (config_key, config_value) VALUES (:key, :value) ON CONFLICT (config_key) DO UPDATE SET config_value=:value, updated_at=NOW()")
    stmt = stmt.bindparams(bindparam("value", type_=JSON))
    await db.execute(stmt, {"key": key, "value": value_obj})
    await db.commit()
    advice = _apply_advice(key)
    return {"code": 0, "message": "saved", "apply": advice}

@router.get("/api/v1/configs")
async def list_configs(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    res = await db.execute(text("SELECT config_key, config_value FROM system_configs ORDER BY config_key LIMIT :limit OFFSET :offset").bindparams(limit=limit, offset=skip))
    rows = res.fetchall()
    data = [{"key": r.config_key, "value": r.config_value} for r in rows]
    return {"code": 0, "message": "success", "data": data}