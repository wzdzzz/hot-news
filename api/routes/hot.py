from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Query

from core.database import (
    get_all_sources,
    get_topic_by_id,
    query_latest_by_source,
    query_topics,
    update_topic_extra,
)

router = APIRouter(prefix="/api/hot", tags=["热点"])

# 分类映射
CATEGORIES = {
    "social": "社交",
    "news": "新闻",
    "tech": "科技",
    "media": "媒体",
}


def success_response(data, message="success"):
    return {"code": 200, "data": data, "message": message}


def parse_date(value: str, is_end: bool = False) -> datetime:
    """解析 ISO 日期串为 naive UTC（与库中存储一致）。

    支持带时区的输入（含 Z 后缀）；纯日期作为结束时间时补到当天 23:59:59。
    """
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if is_end and len(value) == 10:
        dt = dt.replace(hour=23, minute=59, second=59)
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


@router.get("")
def get_hot_topics(
    source: Optional[str] = Query(None, description="来源筛选"),
    category: Optional[str] = Query(None, description="分类筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    start_date: Optional[str] = Query(None, description="开始日期 ISO 格式"),
    end_date: Optional[str] = Query(None, description="结束日期 ISO 格式"),
):
    """获取热点列表（支持筛选、搜索、日期范围、分页）"""
    try:
        parsed_start = parse_date(start_date) if start_date else None
        parsed_end = parse_date(end_date, is_end=True) if end_date else None
    except ValueError:
        return {"code": 400, "data": None, "message": "日期格式无效，请使用 ISO 格式"}

    items, total = query_topics(
        source=source,
        category=category,
        keyword=keyword,
        page=page,
        page_size=page_size,
        start_date=parsed_start,
        end_date=parsed_end,
    )
    return success_response({
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.get("/sources")
def get_sources():
    """获取所有来源列表及状态"""
    sources = get_all_sources()
    return success_response(sources)


@router.get("/categories")
def get_categories():
    """获取所有分类"""
    return success_response(CATEGORIES)


@router.get("/latest")
def get_latest():
    """获取每个来源的最新一批热点"""
    data = query_latest_by_source()
    return success_response(data)


@router.get("/{topic_id}")
def get_topic_detail(topic_id: int):
    """获取单条热点详情"""
    topic = get_topic_by_id(topic_id)
    if topic is None:
        return {"code": 404, "data": None, "message": "Not found"}
    return success_response(topic)


@router.get("/{topic_id}/content")
async def get_topic_content(topic_id: int):
    """抓取并返回文章正文（目前支持 BBC），结果缓存到 extra 字段"""
    topic = get_topic_by_id(topic_id)
    if topic is None:
        return {"code": 404, "data": None, "message": "Not found"}

    # 如果已经缓存过正文，直接返回
    extra = topic.get("extra") or {}
    if extra.get("content"):
        return success_response({
            "title": extra.get("article_title", topic["title"]),
            "content": extra["content"],
            "author": extra.get("author", ""),
            "published_time": extra.get("published_time", ""),
        })

    # 检查来源是否支持正文抓取
    url = topic.get("url", "")
    source = topic.get("source", "")

    if source != "bbc" or not url:
        return {"code": 400, "data": None, "message": f"暂不支持 {source} 来源的正文抓取"}

    try:
        from scrapers.bbc import BBCScraper
        result = await BBCScraper.fetch_article_content(url)

        if not result.get("content"):
            return {"code": 404, "data": None, "message": "未能解析到文章正文"}

        # 缓存到 extra 字段
        update_topic_extra(topic_id, {
            "article_title": result["title"],
            "content": result["content"],
            "author": result["author"],
            "published_time": result["published_time"],
        })

        return success_response(result)
    except Exception as e:
        return {"code": 500, "data": None, "message": f"抓取文章内容失败: {str(e)}"}
