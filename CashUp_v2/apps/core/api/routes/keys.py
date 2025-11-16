from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional

from database.connection import get_db
from utils.crypto import encrypt_str

router = APIRouter()

@router.get("/api/v1/keys")
async def list_keys(exchange: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    try:
        exists = await db.execute(text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='api_keys')"))
        if not exists.scalar_one():
            return {"code": 0, "message": "success", "data": []}
        q = "SELECT id, exchange, name, is_active FROM public.api_keys"
        params = {}
        if exchange:
            q += " WHERE exchange=:exchange"
            params["exchange"] = exchange
        q += " ORDER BY exchange, name"
        res = await db.execute(text(q), params)
        rows = res.fetchall()
        data = [{"id": r.id, "exchange": r.exchange, "name": r.name, "is_active": r.is_active} for r in rows]
        return {"code": 0, "message": "success", "data": data}
    except Exception:
        return {"code": 0, "message": "success", "data": []}

@router.post("/api/v1/keys")
async def upsert_key(payload: dict, db: AsyncSession = Depends(get_db)):
    ex = payload.get("exchange")
    name = payload.get("name", "default")
    key = payload.get("api_key")
    secret = payload.get("api_secret")
    passphrase = payload.get("passphrase")
    enabled = bool(payload.get("enabled", True))
    exists = await db.execute(text("SELECT id FROM public.api_keys WHERE exchange=:ex AND name=:name"), {"ex": ex, "name": name})
    row = exists.first()
    enc_key = encrypt_str(key) if key else None
    enc_secret = encrypt_str(secret) if secret else None
    if row:
        await db.execute(text("UPDATE public.api_keys SET key_data=:key, secret_data=:secret, passphrase=:pass, is_active=:enabled, updated_at=NOW() WHERE id=:id"), {"key": enc_key, "secret": enc_secret, "pass": passphrase, "enabled": enabled, "id": row.id})
    else:
        await db.execute(text("INSERT INTO public.api_keys (user_id, exchange, name, key_data, secret_data, passphrase, is_active) VALUES (NULL, :exchange, :name, :key, :secret, :pass, :enabled)"), {"exchange": ex, "name": name, "key": enc_key, "secret": enc_secret, "pass": passphrase, "enabled": enabled})
    await db.commit()
    return {"code": 0, "message": "saved", "apply": {"type": "reload", "modules": ["exchanges"]}}

@router.put("/api/v1/keys/{id}")
async def update_key(id: int, payload: dict, db: AsyncSession = Depends(get_db)):
    fields = {"key_data": encrypt_str(payload.get("api_key")) if payload.get("api_key") is not None else None, "secret_data": encrypt_str(payload.get("api_secret")) if payload.get("api_secret") is not None else None, "passphrase": payload.get("passphrase"), "is_active": payload.get("enabled")}
    sets = []
    params = {"id": id}
    for k, v in fields.items():
        if v is not None:
            sets.append(f"{k}=:{k}")
            params[k] = v
    if not sets:
        return {"code": 0, "message": "noop"}
    q = f"UPDATE api_keys SET {', '.join(sets)}, updated_at=NOW() WHERE id=:id"
    await db.execute(text(q), params)
    await db.commit()
    return {"code": 0, "message": "updated"}

@router.post("/api/v1/exchanges/reload")
async def reload_exchanges():
    from api.deps import reset_exchange_manager
    reset_exchange_manager()
    return {"code": 0, "message": "reloaded"}