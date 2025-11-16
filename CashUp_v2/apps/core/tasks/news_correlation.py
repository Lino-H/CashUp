from datetime import timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from config.settings import settings
from celery_app import celery_app

engine = create_async_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@celery_app.task(name="tasks.rss.compute_correlation")
def compute_correlation():
    import asyncio
    asyncio.run(_compute_correlation_async())

async def _compute_correlation_async():
    async with SessionLocal() as session:
        news_rows = (await session.execute(text(
            "SELECT id, published_at, sentiment_score, symbols FROM market_news WHERE published_at IS NOT NULL ORDER BY published_at DESC LIMIT 200"
        ))).all()
        for row in news_rows:
            news_id = row.id
            published_at = row.published_at
            sentiment = float(row.sentiment_score or 0)
            symbols = (row.symbols or [])
            for s in symbols:
                # 使用近1小时的K线进行价格变化估算
                before = await session.execute(text(
                    "SELECT close FROM kline_data WHERE symbol=:symbol AND open_time<=:t ORDER BY open_time DESC LIMIT 1"
                ), {"symbol": s.replace("/", "_"), "t": published_at})
                before_close = before.scalar_one_or_none()
                if before_close is None:
                    continue
                after5 = await session.execute(text(
                    "SELECT close FROM kline_data WHERE symbol=:symbol AND open_time>=:t ORDER BY open_time ASC LIMIT 1"
                ), {"symbol": s.replace("/", "_"), "t": published_at + timedelta(minutes=5)})
                after15 = await session.execute(text(
                    "SELECT close FROM kline_data WHERE symbol=:symbol AND open_time>=:t ORDER BY open_time ASC LIMIT 1"
                ), {"symbol": s.replace("/", "_"), "t": published_at + timedelta(minutes=15)})
                after60 = await session.execute(text(
                    "SELECT close FROM kline_data WHERE symbol=:symbol AND open_time>=:t ORDER BY open_time ASC LIMIT 1"
                ), {"symbol": s.replace("/", "_"), "t": published_at + timedelta(hours=1)})
                c5 = after5.scalar_one_or_none()
                c15 = after15.scalar_one_or_none()
                c60 = after60.scalar_one_or_none()
                if c5 is None and c15 is None and c60 is None:
                    continue
                def ch(a):
                    return round(((a - before_close) / before_close) if a is not None else 0, 4)
                change5 = ch(c5)
                change15 = ch(c15)
                change60 = ch(c60)
                corr = (sentiment * (abs(change5) + abs(change15) + abs(change60))) / 3 if before_close else 0
                await session.execute(text(
                    """
                    INSERT INTO news_price_correlation (news_id, exchange, symbol, price_before, price_after_5m, price_change_5m, price_after_15m, price_change_15m, price_after_1h, price_change_1h, correlation_score)
                    VALUES (:news_id, :exchange, :symbol, :pb, :p5, :c5, :p15, :c15, :p60, :c60, :corr)
                    """
                ), {
                    "news_id": news_id,
                    "exchange": "gateio",
                    "symbol": s.replace("/", "_"),
                    "pb": before_close,
                    "p5": c5,
                    "c5": change5,
                    "p15": c15,
                    "c15": change15,
                    "p60": c60,
                    "c60": change60,
                    "corr": corr,
                })
        await session.commit()