from datetime import datetime

from fastapi import APIRouter, Query

from core.database import (
    get_all_sources,
    get_topic_by_id,
    query_latest_by_source,
    query_topics,
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
    source: str | None = Query(None, description="来源筛选"),
    category: str | None = Query(None, description="分类筛选"),
    keyword: str | None = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    start_date: str | None = Query(None, description="开始日期 ISO 格式"),
    end_date: str | None = Query(None, description="结束日期 ISO 格式"),
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
