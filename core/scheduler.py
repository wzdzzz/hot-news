from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from functools import partial

from typing import Dict

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from core.config import get_config, update_scraper_interval
from core.database import save_topics, cleanup_old_data

logger = logging.getLogger(__name__)

# 爬虫运行状态记录
scraper_status: Dict[str, dict] = {}


class ScraperScheduler:
    """爬虫定时调度器"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.config = get_config()

    def setup(self):
        """根据 config.yaml 为每个爬虫创建定时任务"""
        scrapers_config = self.config.get("scrapers", {})

        enabled_index = 0
        for name, cfg in scrapers_config.items():
            if not cfg.get("enabled", False):
                logger.info(f"[{name}] Scraper disabled, skipping")
                continue

            interval = cfg.get("interval", 7200)
            max_items = cfg.get("max_items", 30)

            # 初始化状态
            scraper_status[name] = {
                "last_run": None,
                "last_status": "pending",
                "last_count": 0,
                "last_error": None,
                "interval": interval,
            }

            # interval 触发器首次执行要等满一个周期，启动后错峰安排一次首跑，
            # 避免全新部署长时间无数据
            first_run = datetime.now() + timedelta(seconds=15 + enabled_index * 20)
            self.scheduler.add_job(
                func=self._run_scraper,
                trigger="interval",
                seconds=interval,
                args=[name, max_items],
                id=f"scraper_{name}",
                jitter=120,
                next_run_time=first_run,
                name=f"Scraper: {name}",
            )
            enabled_index += 1
            logger.info(f"[{name}] Scheduled every {interval}s")

        # 每天凌晨3点清理过期数据
        self.scheduler.add_job(
            func=cleanup_old_data,
            trigger="cron",
            hour=3,
            minute=0,
            id="cleanup_old_data",
            name="Cleanup old data",
        )

    async def _run_scraper(self, name: str, max_items: int):
        """执行单个爬虫并存储结果"""
        from scrapers import get_scraper

        logger.info(f"[{name}] Scheduled run started")
        # 手动触发未启用的爬虫时 scraper_status 中没有该项，需先补齐
        status = scraper_status.setdefault(name, {
            "last_run": None,
            "last_status": "pending",
            "last_count": 0,
            "last_error": None,
            "interval": self.config.get("scrapers", {}).get(name, {}).get("interval", 0),
        })
        status["last_run"] = datetime.utcnow().isoformat() + "Z"

        try:
            scraper = get_scraper(name)
            scraper.max_items = max_items
            items = await scraper.run()

            if items:
                # 同步的 SQLAlchemy 写库放到线程池，避免阻塞事件循环
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    None,
                    partial(save_topics, items, source=scraper.source, category=scraper.category),
                )
                status["last_status"] = "success"
                status["last_count"] = len(items)
                status["last_error"] = None
                logger.info(f"[{name}] Completed: {len(items)} items saved")
            else:
                status["last_status"] = "empty"
                status["last_count"] = 0
                status["last_error"] = "Fetched 0 items"
                logger.warning(f"[{name}] Completed with 0 items")

        except Exception as e:
            status["last_status"] = "error"
            status["last_error"] = str(e)
            logger.error(f"[{name}] Failed: {e}")

    def update_interval(self, name: str, interval: int):
        """更新指定爬虫的执行间隔并重新调度"""
        job_id = f"scraper_{name}"
        job = self.scheduler.get_job(job_id)
        if job is None:
            raise KeyError(f"Job '{job_id}' not found in scheduler")

        self.scheduler.reschedule_job(
            job_id,
            trigger="interval",
            seconds=interval,
            jitter=120,
        )
        scraper_status[name]["interval"] = interval
        update_scraper_interval(name, interval)
        logger.info(f"[{name}] Interval updated to {interval}s")

    async def run_scraper_now(self, name: str) -> dict:
        """手动立即执行指定爬虫"""
        from scrapers import get_scraper

        cfg = self.config.get("scrapers", {}).get(name, {})
        max_items = cfg.get("max_items", 30)

        await self._run_scraper(name, max_items)
        return scraper_status.get(name, {})

    def start(self):
        """启动调度器"""
        self.scheduler.start()
        logger.info("Scheduler started")

    def shutdown(self):
        """停止调度器"""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")


# 全局调度器
scheduler = ScraperScheduler()
