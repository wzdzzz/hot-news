from __future__ import annotations

from datetime import datetime
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


@router.get("")
async def get_hot_topics(
    source: Optional[str] = Query(None, description="来源筛选"),
    category: Optional[str] = Query(None, description="分类筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    start_date: Optional[str] = Query(None, description="开始日期 ISO 格式"),
    end_date: Optional[str] = Query(None, description="结束日期 ISO 格式"),
):
    """获取热点列表（支持筛选、搜索、日期范围、分页）"""
    parsed_start = None
    parsed_end = None
    if start_date:
        parsed_start = datetime.fromisoformat(start_date)
    if end_date:
        parsed_end = datetime.fromisoformat(end_date)
        # 如果只传了日期（没有时间部分），自动补到当天 23:59:59
        if parsed_end.hour == 0 and parsed_end.minute == 0 and parsed_end.second == 0:
            parsed_end = parsed_end.replace(hour=23, minute=59, second=59)

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
async def get_sources():
    """获取所有来源列表及状态"""
    sources = get_all_sources()
    return success_response(sources)


@router.get("/categories")
async def get_categories():
    """获取所有分类"""
    return success_response(CATEGORIES)


@router.get("/latest")
async def get_latest():
    """获取每个来源的最新一批热点"""
    data = query_latest_by_source()
    return success_response(data)


@router.get("/{topic_id}")
async def get_topic_detail(topic_id: int):
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
