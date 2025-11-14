import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from config.settings import settings
from celery_app import celery_app
from api.deps import get_exchange_manager

engine = create_async_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@celery_app.task(name="tasks.trading.sync")
def sync_trading():
    asyncio.run(_sync_async())

async def _sync_async():
    mgr = get_exchange_manager()
    async with SessionLocal() as session:
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