"""掘金热榜爬虫"""

import logging

import httpx

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class JuejinScraper(BaseScraper):
    source = "juejin"
    category = "tech"
    base_url = "https://juejin.cn"

    async def fetch(self, client: httpx.AsyncClient) -> list[dict]:
        api = "https://api.juejin.cn/content_api/v1/content/article_rank"
        params = {
            "category_id": "1",
            "type": "hot",
            "count": self.max_items,
        }
        try:
            resp = await client.get(api, params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"[juejin] Request failed: {e}")
            return []

        results: list[dict] = []
        try:
            articles = data.get("data", []) or []
            for idx, item in enumerate(articles, start=1):
                content = item.get("content", {}) or {}
                content_id = content.get("content_id", "") or item.get("content_id", "")
                title = content.get("title", "")
                summary = content.get("brief", "") or content.get("summary", "")
                counter = item.get("content_counter", {}) or {}
                hot_value = counter.get("hot_rank", 0) or counter.get("view", 0)
                image_url = content.get("cover_image", "")

                url = f"https://juejin.cn/post/{content_id}" if content_id else ""

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
                            "content_id": content_id,
                            "category_name": content.get("category_name", ""),
                            "tags": content.get("tags", []),
                        },
                    }
                )
        except Exception as e:
            logger.error(f"[juejin] Parse failed: {e}")
            return []

        return results
