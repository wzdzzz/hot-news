"""今日头条热榜爬虫"""
from __future__ import annotations

import logging

import httpx

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class ToutiaoScraper(BaseScraper):
    source = "toutiao"
    category = "news"
    base_url = "https://www.toutiao.com"

    async def fetch(self, client: httpx.AsyncClient) -> list[dict]:
        api = "https://www.toutiao.com/hot-event/hot-board/"
        params = {"origin": "toutiao_pc"}
        try:
            resp = await client.get(api, params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"[toutiao] Request failed: {e}")
            return []

        results: list[dict] = []
        try:
            items = data.get("data", [])

            for idx, item in enumerate(items, start=1):
                title = item.get("Title", "")
                cluster_id = item.get("ClusterId", "")
                hot_value = item.get("HotValue", 0)
                url = item.get("Url", "")
                if not url and cluster_id:
                    url = f"https://www.toutiao.com/trending/{cluster_id}/"

                image_url = item.get("Image", {}).get("url", "") if isinstance(
                    item.get("Image"), dict
                ) else ""

                label = item.get("Label", "")
                cluster_type = item.get("ClusterType", 0)

                if not title:
                    continue

                results.append(
                    {
                        "title": title,
                        "url": url,
                        "hot_value": hot_value,
                        "rank": idx,
                        "summary": "",
                        "image_url": image_url,
                        "extra": {
                            "cluster_id": cluster_id,
                            "label": label,
                            "cluster_type": cluster_type,
                        },
                    }
                )
        except Exception as e:
            logger.error(f"[toutiao] Parse failed: {e}")
            return []

        return results
