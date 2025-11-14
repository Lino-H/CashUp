"""
新闻与RSS数据模型
"""

from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, text
from sqlalchemy.orm import relationship

from database.connection import Base


class RSSFeed(Base):
    """RSS源配置模型"""
    __tablename__ = "rss_feeds"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False, unique=True)
    category = Column(String(50), nullable=True)
    language = Column(String(10), default="en")
    is_active = Column(Boolean, default=True)
    last_fetch = Column(DateTime, nullable=True)
    fetch_interval = Column(String(20), default="300")
    created_at = Column(DateTime, server_default=func.now())


class MarketNews(Base):
    """市场新闻模型"""
    __tablename__ = "market_news"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    source = Column(String(100), nullable=True)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    url = Column(String(500), nullable=False, unique=True)
    published_at = Column(DateTime, nullable=True)
    category = Column(String(50), nullable=True)
    tags = Column(JSON, nullable=True)
    sentiment_score = Column(String(20), nullable=True)
    sentiment_label = Column(String(20), nullable=True)
    relevance_score = Column(String(20), nullable=True)
    symbols = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())