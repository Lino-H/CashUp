from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from database.connection import get_db

router = APIRouter()

@router.get("/api/v1/strategies/{id}/performance")
async def strategy_performance(id: int, db: AsyncSession = Depends(get_db)):
    q = text("SELECT total_pnl, pnl_rate, total_trades FROM strategy_performance WHERE strategy_id=:id")
    res = await db.execute(q, {"id": id})
    row = res.first()
    if not row:
        return {"code": 404, "message": "not found"}
    return {"code": 0, "message": "success", "data": {"total_pnl": float(row.total_pnl or 0), "pnl_rate": float(row.pnl_rate or 0), "total_trades": int(row.total_trades or 0)}}

@router.get("/api/v1/account/overview")
async def account_overview(db: AsyncSession = Depends(get_db)):
    q = text("SELECT user_id, username, exchange, total_balance, total_available, total_unrealized_pnl, last_updated FROM account_overview")
    res = await db.execute(q)
    rows = res.fetchall()
    data = [{
        "user_id": r.user_id,
        "username": r.username,
        "exchange": r.exchange,
        "total_balance": float(r.total_balance or 0),
        "total_available": float(r.total_available or 0),
        "total_unrealized_pnl": float(r.total_unrealized_pnl or 0),
        "last_updated": r.last_updated.isoformat() if r.last_updated else None,
    } for r in rows]
    return {"code": 0, "message": "success", "data": data}

@router.get("/api/v1/strategies/{id}/statistics")
async def strategy_statistics(id: int, db: AsyncSession = Depends(get_db)):
    # 基于已关闭持仓计算胜率与简易回撤/夏普
    res = await db.execute(text("SELECT realized_pnl, updated_at FROM positions WHERE strategy_instance_id=:id AND status='closed' ORDER BY updated_at ASC"), {"id": id})
    rows = res.fetchall()
    pnl_list = [float(r.realized_pnl or 0) for r in rows]
    wins = len([p for p in pnl_list if p > 0])
    losses = len([p for p in pnl_list if p < 0])
    total = len(pnl_list)
    win_rate = (wins / total) * 100 if total > 0 else 0.0
    equity = []
    s = 0.0
    max_peak = 0.0
    max_drawdown = 0.0
    for p in pnl_list:
        s += p
        equity.append(s)
        if s > max_peak:
            max_peak = s
        dd = (max_peak - s)
        if dd > max_drawdown:
            max_drawdown = dd
    # 简易夏普：平均收益/收益标准差（未年化）
    import math
    mean = (sum(pnl_list) / total) if total > 0 else 0.0
    var = (sum((p - mean) ** 2 for p in pnl_list) / total) if total > 0 else 0.0
    std = math.sqrt(var)
    sharpe = (mean / std) if std > 1e-9 else 0.0
    return {"code": 0, "message": "success", "data": {"win_rate": win_rate, "max_drawdown": max_drawdown, "sharpe_ratio": sharpe, "total_closed": total}}

@router.get("/api/v1/strategies/{id}/equity")
async def strategy_equity(id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(text("SELECT realized_pnl, updated_at FROM positions WHERE strategy_instance_id=:id AND status='closed' ORDER BY updated_at ASC"), {"id": id})
    rows = res.fetchall()
    s = 0.0
    data = []
    for r in rows:
        s += float(r.realized_pnl or 0)
        d = r.updated_at.isoformat() if r.updated_at else None
        data.append({"date": d, "equity": s})
    return {"code": 0, "message": "success", "data": data}

@router.get("/api/v1/strategies/{id}/winrate_series")
async def strategy_winrate_series(id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(text("SELECT realized_pnl, updated_at FROM positions WHERE strategy_instance_id=:id AND status='closed' ORDER BY updated_at ASC"), {"id": id})
    rows = res.fetchall()
    wins = 0
    total = 0
    data = []
    for r in rows:
        pnl = float(r.realized_pnl or 0)
        total += 1
        if pnl > 0:
            wins += 1
        rate = (wins / total) * 100 if total > 0 else 0.0
        d = r.updated_at.isoformat() if r.updated_at else None
        data.append({"date": d, "winRate": rate})
    return {"code": 0, "message": "success", "data": data}