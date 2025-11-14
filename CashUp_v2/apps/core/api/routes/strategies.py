from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Dict, Any

from database.connection import get_db
from api.deps import get_exchanges
from app.adapters.exchanges.base import ExchangeAdapter
from modules.strategy.factors.technical import RSIFactor, MAFactor, EMAFactor
from modules.strategy.factors.momentum import MACDFactor
from modules.strategy.factors.volatility import BollingerFactor, ATRFactor
from modules.strategy.services.manager import CompositeStrategy, lifecycle
from modules.strategy.services.backtest_engine import run_backtest

router = APIRouter()

@router.post("/api/v1/strategies/templates")
async def create_template(body: dict, db: AsyncSession = Depends(get_db)):
    stmt = text("INSERT INTO strategy_templates (name, description, strategy_type, factors, config, code) VALUES (:name, :description, :strategy_type, :factors, :config, :code) RETURNING id")
    res = await db.execute(stmt, {"name": body.get("name"), "description": body.get("description"), "strategy_type": body.get("strategy_type"), "factors": body.get("factors", []), "config": body.get("config", {}), "code": body.get("code")})
    new_id = res.scalar_one()
    return {"code": 0, "message": "策略模板创建成功", "data": {"id": new_id}}

@router.post("/api/v1/strategies/instances")
async def create_instance(body: dict, db: AsyncSession = Depends(get_db)):
    stmt = text("INSERT INTO strategy_instances (user_id, name, description, template_id, exchange, symbol, timeframe, status, config) VALUES (:user_id, :name, :description, :template_id, :exchange, :symbol, :timeframe, 'stopped', :config) RETURNING id")
    res = await db.execute(stmt, {"user_id": 1, "name": body.get("name"), "description": body.get("description"), "template_id": body.get("template_id"), "exchange": body.get("exchange"), "symbol": body.get("symbol"), "timeframe": body.get("timeframe"), "config": body.get("config", {})})
    new_id = res.scalar_one()
    return {"code": 0, "message": "策略实例创建成功", "data": {"id": new_id, "status": "stopped"}}

@router.get("/api/v1/strategies/instances")
async def list_instances(status: str = "running", page: int = 1, page_size: int = 20, db: AsyncSession = Depends(get_db)):
    offset = (page - 1) * page_size
    stmt = text("SELECT id, name, exchange, symbol, timeframe, status, created_at FROM strategy_instances WHERE status = :status ORDER BY created_at DESC LIMIT :limit OFFSET :offset")
    res = await db.execute(stmt.bindparams(limit=page_size, offset=offset), {"status": status})
    items = [{"id": r.id, "name": r.name, "exchange": r.exchange, "symbol": r.symbol, "timeframe": r.timeframe, "status": r.status, "created_at": r.created_at.isoformat() if r.created_at else None} for r in res]
    return {"code": 0, "message": "success", "data": {"total": len(items), "page": page, "page_size": page_size, "items": items}}

@router.post("/api/v1/strategies/instances/{id}/start")
async def start_instance(id: int, exchanges = Depends(get_exchanges), db: AsyncSession = Depends(get_db)):
    row = (await db.execute(text("SELECT name, exchange, symbol, timeframe, config FROM strategy_instances WHERE id=:id"), {"id": id})).first()
    if not row:
        return {"code": 404, "message": "not found"}
    adapter: ExchangeAdapter | None = exchanges.get_exchange(row.exchange)
    if adapter is None:
        return {"code": 1003, "message": f"交易所未配置: {row.exchange}"}
    factors_cfg: List[Dict[str, Any]] = (row.config or {}).get("factors", [])
    factors = []
    for f in factors_cfg:
        if f.get("name") == "rsi":
            p = f.get("params", {})
            factors.append(RSIFactor(period=int(p.get("period", 14)), overbought=float(p.get("overbought", 70)), oversold=float(p.get("oversold", 30))))
        if f.get("name") == "ma":
            p = f.get("params", {})
            factors.append(MAFactor(period=int(p.get("period", 20))))
        if f.get("name") == "macd":
            p = f.get("params", {})
            factors.append(MACDFactor(fast=int(p.get("fast", 12)), slow=int(p.get("slow", 26)), signal=int(p.get("signal", 9))))
        if f.get("name") == "ema":
            p = f.get("params", {})
            factors.append(EMAFactor(period=int(p.get("period", 20))))
        if f.get("name") == "boll":
            p = f.get("params", {})
            factors.append(BollingerFactor(period=int(p.get("period", 20)), mult=float(p.get("mult", 2.0))))
        if f.get("name") == "atr":
            p = f.get("params", {})
            factors.append(ATRFactor(period=int(p.get("period", 14))))
    if not factors:
        factors = [RSIFactor(), MAFactor()]
    composite = CompositeStrategy(row.name, factors)
    comb = (row.config or {}).get("combination", {})
    mode = comb.get("mode")
    if mode in ("weighted", "vote"):
        composite.mode = mode
    weights = comb.get("weights", {})
    for k, v in weights.items():
        try:
            composite.set_weight(k, float(v))
        except Exception:
            pass
    risk = (row.config or {}).get("risk_management", {})
    async with get_db() as session:
        await lifecycle.start(id, adapter, row.symbol, row.timeframe, composite, session, risk)
    await db.execute(text("UPDATE strategy_instances SET status='running', started_at=NOW() WHERE id=:id"), {"id": id})
    return {"code": 0, "message": "策略启动成功", "data": {"id": id, "status": "running"}}

@router.post("/api/v1/strategies/instances/{id}/stop")
async def stop_instance(id: int, db: AsyncSession = Depends(get_db)):
    await lifecycle.stop(id)
    await db.execute(text("UPDATE strategy_instances SET status='stopped', stopped_at=NOW() WHERE id=:id"), {"id": id})
    return {"code": 0, "message": "策略停止成功", "data": {"id": id, "status": "stopped"}}

@router.post("/api/v1/backtest")
async def backtest(body: dict, db: AsyncSession = Depends(get_db)):
    name = body.get("name", "backtest")
    exchange = body.get("exchange")
    symbol = body.get("symbol")
    timeframe = body.get("timeframe")
    start = body.get("start_date")
    end = body.get("end_date")
    factors_cfg: List[Dict[str, Any]] = body.get("factors", [])
    factors = []
    for f in factors_cfg:
        if f.get("name") == "rsi":
            p = f.get("params", {})
            factors.append(RSIFactor(period=int(p.get("period", 14)), overbought=float(p.get("overbought", 70)), oversold=float(p.get("oversold", 30))))
        if f.get("name") == "ma":
            p = f.get("params", {})
            factors.append(MAFactor(period=int(p.get("period", 20))))
        if f.get("name") == "macd":
            p = f.get("params", {})
            factors.append(MACDFactor(fast=int(p.get("fast", 12)), slow=int(p.get("slow", 26)), signal=int(p.get("signal", 9))))
        if f.get("name") == "ema":
            p = f.get("params", {})
            factors.append(EMAFactor(period=int(p.get("period", 20))))
        if f.get("name") == "boll":
            p = f.get("params", {})
            factors.append(BollingerFactor(period=int(p.get("period", 20)), mult=float(p.get("mult", 2.0))))
        if f.get("name") == "atr":
            p = f.get("params", {})
            factors.append(ATRFactor(period=int(p.get("period", 14))))
    if not factors:
        factors = [RSIFactor(), MAFactor()]
    composite = CompositeStrategy(name, factors)
    result = await run_backtest(db, composite, exchange, symbol, timeframe, start, end)
    return {"code": 0, "message": "success", "data": result}