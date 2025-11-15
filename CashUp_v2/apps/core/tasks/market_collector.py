"""
行情采集任务
函数集注释：
- collect_market: 按配置采集 K线数据，批量写库与缓存一致性，失败自动重试与限速
"""
import asyncio
from datetime import datetime, timezone
from typing import List

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from config.settings import settings
from celery_app import celery_app
import os
import yaml
from app.adapters.exchanges.base import ExchangeManager
from database.redis import get_redis

engine = create_async_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def _get_collect_config(session: AsyncSession):
    symbols: List[str] = []
    timeframes: List[str] = ["1h"]
    strategy = "write_through"
    coverage = "upsert"
    window_hours = 24
    try:
        res = await session.execute(text("SELECT config_key, config_value FROM system_configs WHERE config_key IN ('market.collect.symbols','market.collect.timeframes','market.cache.strategy','market.collect.strategy','market.collect.window_hours')"))
        rows = res.fetchall()
        m = {r.config_key: r.config_value for r in rows}
        if isinstance(m.get('market.collect.symbols'), list):
            symbols = [str(s) for s in m['market.collect.symbols']]
        if isinstance(m.get('market.collect.timeframes'), list):
            timeframes = [str(tf) for tf in m['market.collect.timeframes']]
        if m.get('market.cache.strategy'):
            strategy = str(m['market.cache.strategy']).strip('"')
        if m.get('market.collect.strategy'):
            coverage = str(m['market.collect.strategy']).strip('"')
        if m.get('market.collect.window_hours'):
            try:
                window_hours = int(str(m['market.collect.window_hours']).strip('"'))
            except Exception:
                window_hours = 24
    except Exception:
        pass
    return symbols, timeframes, strategy, coverage, window_hours

@celery_app.task(name="tasks.market.collect", autoretry_for=(Exception,), retry_kwargs={"max_retries": 5}, retry_backoff=True, retry_jitter=True, rate_limit="20/m", acks_late=True, time_limit=900)
def collect_market():
    asyncio.run(_collect_async())

def _load_exchanges_config() -> dict:
    path = os.path.join(os.getcwd(), "configs", "exchanges.yaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _build_manager_from_config() -> ExchangeManager:
    cfg = _load_exchanges_config()
    mgr = ExchangeManager()
    for ex_name, conf in (cfg or {}).items():
        if ex_name in ("common", "risk_control", "monitoring"):
            continue
        base_conf = conf if isinstance(conf, dict) else {}
        # 环境变量展开
        for k, v in list(base_conf.items()):
            if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
                env_key = v[2:-1]
                base_conf[k] = os.getenv(env_key, "")
        if bool(base_conf.get("enabled", False)):
            base_conf["name"] = base_conf.get("name", ex_name)
            base_conf["type"] = base_conf.get("type", ex_name)
            mgr.add_exchange(ex_name, base_conf)
    return mgr

async def _collect_async():
    mgr = _build_manager_from_config()
    async with SessionLocal() as session:
        symbols, timeframes, strategy, coverage, window_hours = await _get_collect_config(session)
        # 广播最近运行时间
        try:
            r = await get_redis()
            import time
            await r.set("sched:last:market.collect", str(int(time.time())))
            await r.lpush("sched:history", f"market.collect:{int(time.time())}")
            await r.ltrim("sched:history", 0, 499)
            await r.set("market:collect:started", "1")
            await r.set("market:collect:exchanges", str(len(mgr.get_exchange_names())))
        except Exception:
            pass
        for ex_name in mgr.get_exchange_names():
            adapter = mgr.get_exchange(ex_name)
            if not adapter:
                continue
            # 如果未指定 symbols，则尝试从 YAML 配置中获取
            local_symbols = symbols
            try:
                cfg = adapter.config or {}
                if not local_symbols:
                    local_symbols = cfg.get('symbols', [])
            except Exception:
                pass
            if not local_symbols:
                continue
            for sym in local_symbols:
                for tf in (timeframes or ["1h"]):
                    try:
                        # 频率限制（每交易所-交易对-时间框）：最短间隔 60 秒
                        try:
                            rlim = await get_redis()
                            import time
                            keylim = f"market:collect:last:{ex_name}:{sym.replace('/', '_')}:{tf}"
                            last = await rlim.get(keylim)
                            now = int(time.time())
                            if last is not None and now - int(last) < 60:
                                continue
                            await rlim.set(keylim, str(now))
                        except Exception:
                            pass
                        # 采样窗口（仅写新段）：从最近 open_time 起采集
                        last_row = await session.execute(text("SELECT MAX(open_time) AS last_ot FROM kline_data WHERE exchange=:ex AND symbol=:sym AND timeframe=:tf"), {"ex": ex_name, "sym": sym.replace('/', '_'), "tf": tf})
                        last_ot = last_row.first().last_ot if last_row.first() else None
                        start_dt = None
                        if last_ot:
                            start_dt = last_ot
                            data = await adapter.get_klines(symbol=sym.replace('/', '_'), interval=tf, start_time=start_dt, limit=500)
                        else:
                            data = await adapter.get_klines(symbol=sym.replace('/', '_'), interval=tf, limit=200)
                        try:
                            rdbg = await get_redis()
                            await rdbg.set(f"market:collect:data_count:{ex_name}:{sym.replace('/', '_')}:{tf}", str(len(data)))
                        except Exception:
                            pass
                        # 批量写入数据库（executemany）
                        rows = [
                            {
                                "ex": ex_name,
                                "sym": sym.replace('/', '_'),
                                "tf": tf,
                                "ot": k.open_time,
                                "o": k.open_price,
                                "h": k.high_price,
                                "l": k.low_price,
                                "c": k.close_price,
                                "v": k.volume,
                            }
                            for k in data
                        ]
                        wrote = 0
                        if rows:
                            if coverage == "write_new":
                                await session.execute(
                                    text(
                                        """
                                        INSERT INTO kline_data (exchange, symbol, timeframe, open_time, open, high, low, close, volume)
                                        VALUES (:ex, :sym, :tf, :ot, :o, :h, :l, :c, :v)
                                        ON CONFLICT DO NOTHING
                                        """
                                    ),
                                    rows,
                                )
                            else:
                                await session.execute(
                                    text(
                                        """
                                        INSERT INTO kline_data (exchange, symbol, timeframe, open_time, open, high, low, close, volume)
                                        VALUES (:ex, :sym, :tf, :ot, :o, :h, :l, :c, :v)
                                        ON CONFLICT (exchange, symbol, timeframe, open_time)
                                        DO UPDATE SET open=:o, high=:h, low=:l, close=:c, volume=:v
                                        """
                                    ),
                                    rows,
                                )
                            wrote = len(rows)
                            await session.commit()
                        # 缓存一致性策略
                        if strategy == "write_through":
                            try:
                                r = await get_redis()
                                import json
                                payload = [k.__dict__ for k in data]
                                ck = f"klines:{ex_name}:{sym.replace('/', '_')}:{tf}:100"
                                await r.setex(ck, 30, json.dumps(payload[:100]))
                                await r.set(f"market:collect:wrote:{ex_name}:{sym.replace('/', '_')}:{tf}", str(wrote))
                            except Exception:
                                pass
                    except Exception:
                        try:
                            rerr = await get_redis()
                            import time
                            ts = int(time.time())
                            await rerr.set("market:error:last", str(ts))
                            await rerr.lpush("market:error:history", f"{ex_name}:{sym.replace('/', '_')}:{tf}:{ts}")
                            await rerr.ltrim("market:error:history", 0, 499)
                        except Exception:
                            pass
                        continue