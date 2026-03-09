import logging
from datetime import datetime, timedelta

from sqlalchemy import create_engine, desc, func, select, delete
from sqlalchemy.orm import Session, sessionmaker

from core.config import get_config, get_database_path
from core.models import Base, HotTopic

logger = logging.getLogger(__name__)

# 全局引擎和会话工厂
_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        db_path = get_database_path()
        _engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(_engine)
        logger.info(f"Database initialized at {db_path}")
    return _engine


def get_session() -> Session:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal()


def save_topics(items: list[dict], source: str, category: str):
    """批量保存热点数据到数据库"""
    session = get_session()
    now = datetime.utcnow()
    try:
        for item in items:
            topic = HotTopic(
                source=source,
                category=category,
                title=item.get("title", ""),
                url=item.get("url", ""),
                hot_value=item.get("hot_value", ""),
                rank=item.get("rank", 0),
                summary=item.get("summary", ""),
                image_url=item.get("image_url", ""),
                extra=item.get("extra", {}),
                fetched_at=now,
                created_at=now,
            )
            session.add(topic)
        session.commit()
        logger.info(f"Saved {len(items)} items from {source}")
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to save topics from {source}: {e}")
        raise
    finally:
        session.close()


def query_topics(
    source: str | None = None,
    category: str | None = None,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 20,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> tuple[list[dict], int]:
    """查询热点数据，支持筛选、日期范围和分页"""
    session = get_session()
    try:
        query = session.query(HotTopic)

        if source:
            query = query.filter(HotTopic.source == source)
        if category:
            query = query.filter(HotTopic.category == category)
        if keyword:
            query = query.filter(HotTopic.title.contains(keyword))
        if start_date:
            query = query.filter(HotTopic.fetched_at >= start_date)
        if end_date:
            query = query.filter(HotTopic.fetched_at <= end_date)

        total = query.count()
        items = (
            query.order_by(desc(HotTopic.fetched_at), HotTopic.rank)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return [item.to_dict() for item in items], total
    finally:
        session.close()


def query_latest_by_source() -> dict[str, list[dict]]:
    """获取每个来源的最新一批热点"""
    session = get_session()
    try:
        # 先找到每个来源的最新 fetched_at
        subquery = (
            session.query(
                HotTopic.source,
                func.max(HotTopic.fetched_at).label("max_fetched"),
            )
            .group_by(HotTopic.source)
            .subquery()
        )

        items = (
            session.query(HotTopic)
            .join(
                subquery,
                (HotTopic.source == subquery.c.source)
                & (HotTopic.fetched_at == subquery.c.max_fetched),
            )
            .order_by(HotTopic.source, HotTopic.rank)
            .all()
        )

        result: dict[str, list[dict]] = {}
        for item in items:
            result.setdefault(item.source, []).append(item.to_dict())
        return result
    finally:
        session.close()


def get_topic_by_id(topic_id: int) -> dict | None:
    """根据 ID 获取单条热点"""
    session = get_session()
    try:
        topic = session.query(HotTopic).get(topic_id)
        return topic.to_dict() if topic else None
    finally:
        session.close()


def update_topic_extra(topic_id: int, extra: dict) -> bool:
    """更新热点的 extra 字段（用于缓存文章正文等）"""
    session = get_session()
    try:
        topic = session.query(HotTopic).get(topic_id)
        if topic is None:
            return False
        # 合并已有 extra 数据
        current_extra = topic.extra or {}
        current_extra.update(extra)
        topic.extra = current_extra
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to update extra for topic {topic_id}: {e}")
        return False
    finally:
        session.close()


def get_all_sources() -> list[dict]:
    """获取所有来源及其最后更新时间和条目数"""
    session = get_session()
    try:
        results = (
            session.query(
                HotTopic.source,
                HotTopic.category,
                func.count(HotTopic.id).label("total_count"),
                func.max(HotTopic.fetched_at).label("last_fetched"),
            )
            .group_by(HotTopic.source)
            .all()
        )
        return [
            {
                "source": r.source,
                "category": r.category,
                "total_count": r.total_count,
                "last_fetched": r.last_fetched.isoformat() if r.last_fetched else None,
            }
            for r in results
        ]
    finally:
        session.close()


def cleanup_old_data():
    """清理过期数据"""
    cfg = get_config()
    days = cfg.get("database", {}).get("cleanup_days", 30)
    cutoff = datetime.utcnow() - timedelta(days=days)
    session = get_session()
    try:
        deleted = (
            session.query(HotTopic)
            .filter(HotTopic.created_at < cutoff)
            .delete()
        )
        session.commit()
        logger.info(f"Cleaned up {deleted} old records (older than {days} days)")
    except Exception as e:
        session.rollback()
        logger.error(f"Cleanup failed: {e}")
    finally:
        session.close()
