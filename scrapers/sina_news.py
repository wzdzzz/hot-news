"""新浪新闻热榜爬虫"""
from __future__ import annotations

import logging

import httpx

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class SinaNewsScraper(BaseScraper):
    source = "sina_news"
    category = "news"
    base_url = "https://newsapp.sina.cn"

    async def fetch(self, client: httpx.AsyncClient) -> list[dict]:
        api = "https://newsapp.sina.cn/api/hotlist?newsId=HB-1-snhs%2FSD-1-snhs"
        try:
            resp = await client.get(api)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"[sina_news] Request failed: {e}")
            return []

        results: list[dict] = []
        try:
            # 新浪热榜接口返回 data.hotList 或 data 直接为列表
            hot_list = data.get("data", {})
            if isinstance(hot_list, dict):
                hot_list = hot_list.get("hotList", []) or hot_list.get("list", [])
            if not isinstance(hot_list, list):
                hot_list = []

            for idx, item in enumerate(hot_list, start=1):
                info = item.get("info", item)
                title = info.get("title", "") or item.get("title", "")
                url = info.get("url", "") or item.get("url", "")
                hot_value = info.get("hotValue", 0) or item.get("hotValue", 0)
                summary = info.get("digest", "") or info.get("summary", "")
                image_url = info.get("pic", "") or info.get("image", "")

                if not title:
                    continue

                results.append(
                    {
                        "title": title,
                        "url": url,
                        "hot_value": hot_value,
                        "rank": idx,
                        "summary": summary,
                        "image_url": image_url,
                        "extra": {
                            "media": info.get("media", ""),
                            "category": info.get("category", ""),
                        },
                    }
                )
        except Exception as e:
            logger.error(f"[sina_news] Parse failed: {e}")
            return []

        return results
