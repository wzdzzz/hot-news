from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class HotTopic(Base):
    __tablename__ = "hot_topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)
    category = Column(String(30), nullable=False)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), default="")
    hot_value = Column(String(50), default="")
    rank = Column(Integer, default=0)
    summary = Column(Text, default="")
    image_url = Column(String(1000), default="")
    extra = Column(JSON, default=dict)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_source_title_fetched", "source", "title", "fetched_at"),
        Index("idx_source_fetched", "source", "fetched_at"),
        Index("idx_category", "category"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "category": self.category,
            "title": self.title,
            "url": self.url,
            "hot_value": self.hot_value,
            "rank": self.rank,
            "summary": self.summary,
            "image_url": self.image_url,
            "extra": self.extra,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
