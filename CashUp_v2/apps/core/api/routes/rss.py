from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.connection import get_db
from models.news import RSSFeed

router = APIRouter()

@router.get('/api/v1/rss/feeds')
async def list_feeds(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(RSSFeed))).scalars().all()
    items = [{
        'id': str(r.id),
        'name': r.name,
        'url': r.url,
        'category': r.category,
        'is_active': r.is_active,
    } for r in rows]
    return {'code': 0, 'message': 'success', 'data': items}