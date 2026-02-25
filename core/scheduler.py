import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from core.config import get_config
from core.database import save_topics, cleanup_old_data

logger = logging.getLogger(__name__)

# 爬虫运行状态记录
scraper_status: dict[str, dict] = {}


class ScraperScheduler:
    """爬虫定时调度器"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.config = get_config()

    def setup(self):
        """根据 config.yaml 为每个爬虫创建定时任务"""
        from scrapers import get_scraper

        scrapers_config = self.config.get("scrapers", {})

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

            self.scheduler.add_job(
                func=self._run_scraper,
                trigger="interval",
                seconds=interval,
                args=[name, max_items],
                id=f"scraper_{name}",
                jitter=120,
                name=f"Scraper: {name}",
            )
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
        scraper_status[name]["last_run"] = datetime.utcnow().isoformat()

        try:
            scraper = get_scraper(name)
            scraper.max_items = max_items
            items = await scraper.run()

            if items:
                save_topics(items, source=scraper.source, category=scraper.category)
                scraper_status[name]["last_status"] = "success"
                scraper_status[name]["last_count"] = len(items)
                scraper_status[name]["last_error"] = None
                logger.info(f"[{name}] Completed: {len(items)} items saved")
            else:
                scraper_status[name]["last_status"] = "empty"
                scraper_status[name]["last_count"] = 0
                scraper_status[name]["last_error"] = "Fetched 0 items"
                logger.warning(f"[{name}] Completed with 0 items")

        except Exception as e:
            scraper_status[name]["last_status"] = "error"
            scraper_status[name]["last_error"] = str(e)
            logger.error(f"[{name}] Failed: {e}")

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
