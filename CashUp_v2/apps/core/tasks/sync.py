import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from config.settings import settings
from celery_app import celery_app
from database.redis import get_redis
from api.deps import get_exchange_manager

engine = create_async_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@celery_app.task(name="tasks.trading.sync")
def sync_trading():
    asyncio.run(_sync_async())

async def _sync_async():
    mgr = get_exchange_manager()
    async with SessionLocal() as session:
        # 读取动态间隔
        interval_sec = 60
        try:
            res = await session.execute(text("SELECT config_value FROM system_configs WHERE config_key='trading.sync.interval'"))
            row = res.first()
            if row and row.config_value:
                try:
                    interval_sec = int(str(row.config_value).strip('"'))
                except Exception:
                    pass
        except Exception:
            pass
        # 软重载节流：在 Redis 记录上次执行时间戳
        try:
            r = await get_redis()
            import time
            last = await r.get("trading_sync:last_run")
            now = int(time.time())
            if last is not None:
                last_i = int(last)
                if now - last_i < interval_sec:
                    return
            await r.set("trading_sync:last_run", str(now))
            await r.set("sched:last:trading.sync", str(now))
        except Exception:
            pass
        for name in mgr.get_exchange_names():
            adapter = mgr.get_exchange(name)
            if not adapter:
                continue
            # 重试获取余额
            for attempt in range(3):
                try:
                    balances = await adapter.get_balance()
                    for asset, bal in balances.items():
                        await session.execute(text(
                            """
                            INSERT INTO account_balances (user_id, exchange, asset, balance, available, locked, updated_at)
                            VALUES (1, :exchange, :asset, :balance, :available, :locked, NOW())
                            ON CONFLICT (user_id, exchange, asset) DO UPDATE SET balance=EXCLUDED.balance, available=EXCLUDED.available, locked=EXCLUDED.locked, updated_at=NOW()
                            """
                        ), {"exchange": name, "asset": bal.asset, "balance": bal.total, "available": bal.free, "locked": bal.used})
                    break
                except Exception:
                    await asyncio.sleep(2 ** attempt)
            # 更新持仓价格与浮盈
            open_rows = await session.execute(text("SELECT id, symbol, strategy_instance_id, quantity, entry_price FROM positions WHERE exchange=:exchange AND status='open'"), {"exchange": name})
            for r in open_rows:
                for attempt in range(2):
                    try:
                        t = await adapter.get_ticker(r.symbol)
                        mark = t.last_price
                        qty = float(r.quantity or 0)
                        entry = float(r.entry_price or 0)
                        pnl = (mark - entry) * qty
                        await session.execute(text("UPDATE positions SET mark_price=:mark, unrealized_pnl=:pnl, updated_at=NOW() WHERE id=:id"), {"mark": mark, "pnl": pnl, "id": r.id})
                        break
                    except Exception:
                        await asyncio.sleep(1)
            await session.commit()