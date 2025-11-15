from fastapi import APIRouter, Depends, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from database.connection import get_db
from database.redis import get_redis
from celery_app import celery_app

router = APIRouter()

@router.get("/api/v1/scheduler/status")
async def scheduler_status(granularity: str = Query(default="hour"), task: str = Query(default=None), feed_id: str = Query(default=None), db: AsyncSession = Depends(get_db)):
    res = await db.execute(text("SELECT config_key, config_value FROM system_configs WHERE config_key LIKE '%%.interval'"))
    rows = res.fetchall()
    intervals = {r.config_key: r.config_value for r in rows}
    last = {}
    history = []
    task_trend = {}
    try:
        r = await get_redis()
        for k in ['rss.fetch', 'rss.analyze', 'rss.correlation', 'trading.sync', 'market.collect']:
            v = await r.get(f"sched:last:{k}")
            last[k] = int(v) if v else None
        hist = await r.lrange('sched:history', 0, 199)
        for h in hist or []:
            try:
                s = h.decode() if isinstance(h, (bytes, bytearray)) else str(h)
                name, ts = s.split(':')
                if task and name != task:
                    continue
                history.append({"task": name, "timestamp": int(ts)})
                # 任务趋势聚合
                unit = 86400 if granularity == 'day' else 3600
                b = int(ts) - (int(ts) % unit)
                task_trend.setdefault(name, {})
                task_trend[name][b] = task_trend[name].get(b, 0) + 1
            except Exception:
                continue
        err_total = await r.get("rss:error_total")
        err_last = await r.get("rss:error:last")
        err_per_feed = await r.hgetall("rss:error:feed")
        err_hist_raw = await r.lrange("rss:error:history", 0, 199)
        m_err_last = await r.get("market:error:last")
        m_err_hist_raw = await r.lrange("market:error:history", 0, 199)
        buckets = {}
        m_buckets = {}
        import time
        now = int(time.time())
        for it in err_hist_raw or []:
            try:
                s = it.decode() if isinstance(it, (bytes, bytearray)) else str(it)
                parts = s.split(':')
                if len(parts) == 3 and parts[0] == 'feed':
                    fid = parts[1]
                    ts = int(parts[2])
                    if feed_id and fid != feed_id:
                        continue
                else:
                    ts = int(parts[-1])
                if granularity == 'day':
                    unit = 86400
                else:
                    unit = 3600
                bucket = ts - (ts % unit)
                buckets[bucket] = buckets.get(bucket, 0) + 1
            except Exception:
                continue
        for it in m_err_hist_raw or []:
            try:
                s = it.decode() if isinstance(it, (bytes, bytearray)) else str(it)
                parts = s.split(':')
                # 格式 ex:symbol:tf:ts
                ts = int(parts[-1])
                unit = 86400 if granularity == 'day' else 3600
                bucket = ts - (ts % unit)
                m_buckets[bucket] = m_buckets.get(bucket, 0) + 1
            except Exception:
                continue
        errors = {
            "total": int(err_total) if err_total else 0,
            "last": int(err_last) if err_last else None,
            "per_feed": {k.decode(): int(v.decode()) for k, v in (err_per_feed or {}).items()} if isinstance(err_per_feed, dict) else {},
            "trend": buckets,
            "market_last": int(m_err_last) if m_err_last else None,
            "market_trend": m_buckets,
        }
    except Exception:
        errors = {"total": 0, "last": None, "per_feed": {}, "market_last": None, "market_trend": {}}
    fallback = []
    try:
        r2 = await db.execute(text("SELECT config_value FROM system_configs WHERE config_key='rss.fallback.feeds'"))
        row2 = r2.first()
        if row2 and row2.config_value:
            if isinstance(row2.config_value, list):
                fallback = row2.config_value
    except Exception:
        fallback = []
    # series 结构化输出
    task_series = [{"name": k, "points": sorted([{"bucket": b, "count": c} for b, c in v.items()], key=lambda x: x["bucket"])} for k, v in task_trend.items()]
    error_series = sorted([{"bucket": b, "count": c} for b, c in (errors.get("trend", {}) or {}).items()], key=lambda x: x["bucket"])
    market_error_series = sorted([{"bucket": b, "count": c} for b, c in (errors.get("market_trend", {}) or {}).items()], key=lambda x: x["bucket"])
    return {"code": 0, "message": "success", "data": {"intervals": intervals, "last": last, "errors": errors, "fallback": fallback, "history": history, "task_series": task_series, "error_series": error_series, "market_error_series": market_error_series}}

@router.post("/api/v1/scheduler/trigger")
async def scheduler_trigger(payload: dict = Body(...)):
    task = (payload or {}).get("task")
    mapping = {
        "rss.fetch": "tasks.rss.fetch_feeds",
        "rss.analyze": "tasks.rss.analyze_sentiment",
        "rss.correlation": "tasks.rss.compute_correlation",
        "trading.sync": "tasks.trading.sync",
        "market.collect": "tasks.market.collect",
    }
    if task not in mapping:
        return {"code": 400, "message": "invalid task"}
    celery_app.send_task(mapping[task])
    return {"code": 0, "message": "queued", "data": {"task": task}}