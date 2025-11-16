"""
新闻API路由
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from database.connection import get_db
from models.news import MarketNews


router = APIRouter()


@router.get("/news")
async def list_news(
    symbol: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    sentiment: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """获取新闻列表"""
    stmt = select(MarketNews).order_by(MarketNews.published_at.desc())

    if symbol:
        stmt = stmt.where(MarketNews.symbols.contains([symbol]))
    if category:
        stmt = stmt.where(MarketNews.category == category)
    if sentiment:
        stmt = stmt.where(MarketNews.sentiment_label == sentiment)

    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    items = result.scalars().all()

    data = [
        {
            "id": str(item.id),
            "source": item.source,
            "title": item.title,
            "summary": item.summary,
            "url": item.url,
            "published_at": item.published_at.isoformat() if item.published_at else None,
            "category": item.category,
            "sentiment_score": item.sentiment_score,
            "sentiment_label": item.sentiment_label,
            "symbols": item.symbols or [],
        }
        for item in items
    ]
    return {"code": 0, "message": "success", "data": data}


@router.get("/news/{news_id}")
async def get_news_detail(news_id: str, db: AsyncSession = Depends(get_db)):
    """获取新闻详情"""
    stmt = select(MarketNews).where(MarketNews.id == news_id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    if not item:
        return {"code": 404, "message": "not found"}
    data = {
        "id": str(item.id),
        "source": item.source,
        "title": item.title,
        "content": item.content,
        "summary": item.summary,
        "url": item.url,
        "published_at": item.published_at.isoformat() if item.published_at else None,
        "category": item.category,
        "tags": item.tags or [],
        "sentiment_score": item.sentiment_score,
        "sentiment_label": item.sentiment_label,
        "relevance_score": item.relevance_score,
        "symbols": item.symbols or [],
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }
    return {"code": 0, "message": "success", "data": data}