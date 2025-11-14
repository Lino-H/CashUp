"""
RSS新闻抓取与情绪分析任务
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


@celery_app.task(name="tasks.rss.fetch_feeds")
def fetch_feeds():
    asyncio.run(_fetch_feeds_async())


async def _fetch_feeds_async():
    async with SessionLocal() as session:
        feeds = (await session.execute(select(RSSFeed).where(RSSFeed.is_active == True))).scalars().all()
        if not feeds:
            return
        async with aiohttp.ClientSession() as client:
            for feed in feeds:
                try:
                    async with client.get(feed.url, timeout=30) as resp:
                        content = await resp.text()
                        parsed = await asyncio.to_thread(feedparser.parse, content)
                        for entry in parsed.entries:
                            url = entry.get("link")
                            if not url:
                                continue
                            # 去重
                            exists = (await session.execute(select(MarketNews).where(MarketNews.url == url))).scalar_one_or_none()
                            if exists:
                                continue
                            # 摘要与发布时间
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
                        saved = (await session.execute(select(MarketNews).where(MarketNews.url == url))).scalar_one_or_none()
                        if saved:
                            try:
                                from events.notifications import publish
                                await publish("news.published", {"news_id": str(saved.id), "title": saved.title, "symbols": saved.symbols or []})
                            except Exception:
                                pass
                    feed.last_fetch = datetime.utcnow()
                    await session.commit()
                except Exception:
                    continue


@celery_app.task(name="tasks.rss.analyze_sentiment")
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