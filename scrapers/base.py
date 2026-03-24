from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import httpx

from core.anti_detect import get_headers, random_delay, rate_limit_wait
from core.proxy import proxy_manager

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """所有爬虫的抽象基类"""

    source: str = ""        # 来源标识，如 "weibo"
    category: str = ""      # 分类: social / news / tech / media
    base_url: str = ""      # 目标网站地址
    max_items: int = 50     # 默认最大抓取条数

    @abstractmethod
    async def fetch(self, client: httpx.AsyncClient) -> list[dict]:
        """
        子类实现具体的爬取逻辑。

        返回标准化的字典列表:
        [
            {
                "title": "标题",
                "url": "原文链接",
                "hot_value": "热度值",
                "rank": 1,
                "summary": "摘要",
                "image_url": "封面图",
                "extra": {}
            }
        ]
        """
        ...

    async def run(self) -> list[dict]:
        """执行爬取，包装反爬逻辑"""
        logger.info(f"[{self.source}] Starting scrape...")

        await rate_limit_wait(self.source)
        await random_delay(self.source)

        headers = get_headers(referer=self.base_url)
        proxy = proxy_manager.get_proxy()

        transport = httpx.AsyncHTTPTransport(proxy=proxy) if proxy else None
        async with httpx.AsyncClient(
            headers=headers,
            transport=transport,
            timeout=30,
            follow_redirects=True,
        ) as client:
            try:
                items = await self.fetch(client)
                # 限制条数
                items = items[: self.max_items]
                logger.info(f"[{self.source}] Fetched {len(items)} items")
                return items
            except Exception as e:
                logger.error(f"[{self.source}] Scrape failed: {e}")
                return []
