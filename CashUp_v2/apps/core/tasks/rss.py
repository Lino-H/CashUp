"""
RSS新闻抓取与情绪分析任务
函数集注释：
- fetch_feeds: 抓取 RSS 源并入库，失败自动重试与限速
- analyze_sentiment: 对未标注新闻进行情绪分析，失败自动重试与限速
"""

import asyncio
from datetime import datetime
from typing import Dict, List

import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from snownlp import SnowNLP
import aiohttp

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from config.settings import settings
from models.news import MarketNews, RSSFeed
from celery_app import celery_app
from database.redis import get_redis


analyzer = SentimentIntensityAnalyzer()


def _extract_symbols(text: str) -> List[str]:
    symbols = []
    t = (text or "").lower()
    mapping = {
        "btc": "BTC/USDT",
        "bitcoin": "BTC/USDT",
        "eth": "ETH/USDT",
        "ethereum": "ETH/USDT",
        "bnb": "BNB/USDT",
        "sol": "SOL/USDT",
    }
    for k, v in mapping.items():
        if k in t:
            symbols.append(v)
    return list(set(symbols))


engine = create_async_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@celery_app.task(name="tasks.rss.fetch_feeds", autoretry_for=(Exception,), retry_kwargs={"max_retries": 5}, retry_backoff=True, retry_jitter=True, rate_limit="30/m", acks_late=True, time_limit=600)
def fetch_feeds():
    asyncio.run(_fetch_feeds_async())


async def _fetch_feeds_async():
    async with SessionLocal() as session:
        try:
            r = await get_redis()
            import time
            await r.set("sched:last:rss.fetch", str(int(time.time())))
        except Exception:
            pass
        feeds = (await session.execute(select(RSSFeed).where(RSSFeed.is_active == True))).scalars().all()
        fallback_urls = []
        try:
            from sqlalchemy import text
            res = await session.execute(text("SELECT config_value FROM system_configs WHERE config_key='rss.fallback.feeds'"))
            row = res.first()
            if row and row.config_value:
                fv = row.config_value
                if isinstance(fv, list):
                    fallback_urls = [str(u) for u in fv if isinstance(u, str)]
        except Exception:
            fallback_urls = []
        if not feeds:
            if not fallback_urls:
                return
        async with aiohttp.ClientSession() as client:
            for feed in feeds:
                try:
                    content = None
                    attempts = 0
                    while attempts < 3 and content is None:
                        try:
                            async with client.get(feed.url, timeout=30) as resp:
                                if resp.status == 200:
                                    content = await resp.text()
                                else:
                                    content = None
                        except Exception:
                            content = None
                        if content is None:
                            attempts += 1
                            await asyncio.sleep(2 ** attempts)
                    if content is None:
                        try:
                            import httpx
                            async with httpx.AsyncClient(timeout=30) as hc:
                                r2 = await hc.get(feed.url)
                                if r2.status_code == 200:
                                    content = r2.text
                        except Exception:
                            content = None
                    if content is None:
                        if fallback_urls:
                            for u in fallback_urls:
                                try:
                                    async with client.get(u, timeout=30) as resp2:
                                        if resp2.status == 200:
                                            content = await resp2.text()
                                            feed = RSSFeed(id=0, name="fallback", url=u, category="general")
                                            break
                                except Exception:
                                    continue
                        if content is None:
                            try:
                                import httpx
                                async with httpx.AsyncClient(timeout=30) as hc:
                                    r2 = await hc.get(feed.url)
                                    if r2.status_code == 200:
                                        content = r2.text
                            except Exception:
                                content = None
                        if content is None:
                            try:
                                rr = await get_redis()
                                await rr.incr("rss:error_total")
                                fid = str(getattr(feed, 'id', 'fallback'))
                                await rr.hincrby("rss:error:feed", fid, 1)
                                import time
                                ts = int(time.time())
                                await rr.set("rss:error:last", str(ts))
                                await rr.lpush("rss:error:history", f"feed:{fid}:{ts}")
                                await rr.ltrim("rss:error:history", 0, 499)
                            except Exception:
                                pass
                            continue
                        parsed = await asyncio.to_thread(feedparser.parse, content)
                        for entry in parsed.entries:
                            url = entry.get("link")
                            if not url:
                                continue
                            exists = (await session.execute(select(MarketNews).where(MarketNews.url == url))).scalar_one_or_none()
                            if exists:
                                continue
                            summary = entry.get("summary", "")
                            published_at = None
                            if entry.get("published_parsed"):
                                published_at = datetime(*entry.published_parsed[:6])
                            title = entry.get("title", "")
                            symbols = _extract_symbols(title + " " + summary)
                            item = MarketNews(
                                source=feed.name,
                                title=title,
                                summary=summary,
                                url=url,
                                published_at=published_at,
                                category=feed.category,
                                symbols=symbols,
                                metadata={"feed_id": str(feed.id), "guid": entry.get("id", "")},
                            )
                            session.add(item)
                        await session.commit()
                        try:
                            saved_items = (await session.execute(select(MarketNews).where(MarketNews.source == feed.name).order_by(MarketNews.created_at.desc()))).scalars().all()
                            for si in saved_items[:5]:
                                try:
                                    from events.notifications import publish
                                    await publish("news.published", {"news_id": str(si.id), "title": si.title, "symbols": si.symbols or []})
                                except Exception:
                                    continue
                        except Exception:
                            pass
                        feed.last_fetch = datetime.utcnow()
                        await session.commit()
                except Exception:
                    try:
                        rr = await get_redis()
                        await rr.incr("rss:error_total")
                        fid = str(getattr(feed, 'id', 'fallback'))
                        await rr.hincrby("rss:error:feed", fid, 1)
                        import time
                        ts = int(time.time())
                        await rr.set("rss:error:last", str(ts))
                        await rr.lpush("rss:error:history", f"feed:{fid}:{ts}")
                        await rr.ltrim("rss:error:history", 0, 499)
                    except Exception:
                        pass
                    continue


@celery_app.task(name="tasks.rss.analyze_sentiment", autoretry_for=(Exception,), retry_kwargs={"max_retries": 5}, retry_backoff=True, retry_jitter=True, rate_limit="100/m", acks_late=True, time_limit=600)
def analyze_sentiment():
    asyncio.run(_analyze_sentiment_async())


async def _analyze_sentiment_async():
    async with SessionLocal() as session:
        items = (await session.execute(select(MarketNews).where(MarketNews.sentiment_label == None))).scalars().all()
        for item in items:
            text = (item.title or "") + " " + (item.summary or "")
            score = 0.0
            label = "neutral"
            if text:
                try:
                    vs = analyzer.polarity_scores(text)
                    score = vs.get("compound", 0.0)
                    label = "positive" if score >= 0.2 else "negative" if score <= -0.2 else "neutral"
                except Exception:
                    pass
                try:
                    s = SnowNLP(text)
                    cn = s.sentiments
                    # 简单融合
                    score = (score + (cn - 0.5) * 2) / 2
                    label = "positive" if score >= 0.2 else "negative" if score <= -0.2 else "neutral"
                except Exception:
                    pass
            item.sentiment_score = f"{score:.3f}"
            item.sentiment_label = label
            session.add(item)
        await session.commit()