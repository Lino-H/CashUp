import asyncio
import time
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from config.settings import settings
from celery_app import celery_app
from database.redis import get_redis

engine = create_async_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

def _to_int(v, d):
    try:
        return int(str(v).strip('"'))
    except Exception:
        return d

async def _get_intervals(session: AsyncSession):
    keys = [
        'rss.fetch.interval',
        'rss.analyze.interval',
        'rss.correlation.interval',
        'trading.sync.interval',
        'market.collect.interval',
    ]
    res = await session.execute(text("SELECT config_key, config_value FROM system_configs WHERE config_key = ANY(:arr)").bindparams(arr=keys))
    rows = res.fetchall()
    m = {r.config_key: r.config_value for r in rows}
    return {
        'rss.fetch': _to_int(m.get('rss.fetch.interval'), 300),
        'rss.analyze': _to_int(m.get('rss.analyze.interval'), 600),
        'rss.correlation': _to_int(m.get('rss.correlation.interval'), 900),
        'trading.sync': _to_int(m.get('trading.sync.interval'), 60),
        'market.collect': _to_int(m.get('market.collect.interval'), 300),
    }

async def _heartbeat_async():
    async with SessionLocal() as session:
        intervals = await _get_intervals(session)
        r = None
        try:
            r = await get_redis()
        except Exception:
            pass
        now = int(time.time())
        def should_run(k, iv):
            if r is None:
                return True
            async def inner():
                last = await r.get(f"sched:last:{k}")
                if last is not None:
                    if now - int(last) < iv:
                        return False
                await r.set(f"sched:last:{k}", str(now))
                return True
            return inner()
        async def enqueue(name, task):
            celery_app.send_task(task)
            if r is not None:
                await r.lpush('sched:history', f"{name}:{now}")
                await r.ltrim('sched:history', 0, 199)
        if await should_run('rss.fetch', intervals['rss.fetch']):
            await enqueue('rss.fetch', 'tasks.rss.fetch_feeds')
        if await should_run('rss.analyze', intervals['rss.analyze']):
            await enqueue('rss.analyze', 'tasks.rss.analyze_sentiment')
        if await should_run('rss.correlation', intervals['rss.correlation']):
            await enqueue('rss.correlation', 'tasks.rss.compute_correlation')
        if await should_run('trading.sync', intervals['trading.sync']):
            await enqueue('trading.sync', 'tasks.trading.sync')
        if await should_run('market.collect', intervals['market.collect']):
            await enqueue('market.collect', 'tasks.market.collect')

@celery_app.task(name="tasks.scheduler.heartbeat")
def scheduler_heartbeat():
    asyncio.run(_heartbeat_async())