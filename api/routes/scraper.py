import asyncio

from fastapi import APIRouter, Body
from pydantic import BaseModel, Field

from core.scheduler import scheduler, scraper_status
from scrapers import SCRAPER_MAP


class IntervalUpdate(BaseModel):
    source: str
    interval: int = Field(..., ge=60, le=86400)

router = APIRouter(prefix="/api/scraper", tags=["爬虫管理"])


def success_response(data, message="success"):
    return {"code": 200, "data": data, "message": message}


@router.get("/status")
async def get_scraper_status():
    """查看所有爬虫的运行状态"""
    return success_response(scraper_status)


@router.post("/run")
async def run_scraper(
    source: str = Body(..., embed=True, description="爬虫来源名称"),
):
    """手动触发指定爬虫"""
    if source not in SCRAPER_MAP:
        return {"code": 400, "data": None, "message": f"Unknown scraper: {source}"}

    result = await scheduler.run_scraper_now(source)
    return success_response(result, message=f"Scraper {source} executed")


@router.post("/interval")
async def update_scraper_interval(body: IntervalUpdate):
    """修改爬虫执行间隔（秒），范围 60~86400"""
    if body.source not in scraper_status:
        return {"code": 400, "data": None, "message": f"Unknown scraper: {body.source}"}
    try:
        scheduler.update_interval(body.source, body.interval)
        return success_response(
            scraper_status[body.source],
            message=f"Interval of {body.source} updated to {body.interval}s",
        )
    except Exception as e:
        return {"code": 500, "data": None, "message": str(e)}


@router.post("/run-all")
async def run_all_scrapers():
    """手动触发所有启用的爬虫（并发执行）"""

    async def _run_one(name: str):
        result = await scheduler.run_scraper_now(name)
        return name, result

    tasks = [_run_one(name) for name in scraper_status]
    done = await asyncio.gather(*tasks, return_exceptions=True)

    results = {}
    for item in done:
        if isinstance(item, Exception):
            continue
        name, result = item
        results[name] = result

    return success_response(results, message="All scrapers executed")
