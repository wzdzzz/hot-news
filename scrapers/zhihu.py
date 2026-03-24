"""知乎热榜爬虫"""
from __future__ import annotations

import logging

import httpx

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class ZhihuScraper(BaseScraper):
    source = "zhihu"
    category = "social"
    base_url = "https://www.zhihu.com"

    async def fetch(self, client: httpx.AsyncClient) -> list[dict]:
        api = "https://api.zhihu.com/topstory/hot-list"
        params = {"limit": self.max_items}
        try:
            resp = await client.get(api, params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"[zhihu] Request failed: {e}")
            return []

        results: list[dict] = []
        try:
            items = data.get("data", [])
            for idx, item in enumerate(items, start=1):
                target = item.get("target", {})
                title = target.get("title", "")
                question_id = target.get("id", "")
                excerpt = target.get("excerpt", "")

                detail_text = item.get("detail_text", "")
                # detail_text is like "xxx 万热度"
                hot_value = detail_text.replace("万热度", "").strip()

                children = item.get("children", [])
                image_url = ""
                if children:
                    thumb = children[0].get("thumbnail", "")
                    if thumb:
                        image_url = thumb

                # Fallback image from target
                if not image_url:
                    bound_top_img = target.get("bound_top_img", "")
                    if bound_top_img:
                        image_url = bound_top_img

                url = f"https://www.zhihu.com/question/{question_id}" if question_id else ""

                results.append(
                    {
                        "title": title,
                        "url": url,
                        "hot_value": hot_value,
                        "rank": idx,
                        "summary": excerpt,
                        "image_url": image_url,
                        "extra": {
                            "detail_text": detail_text,
                            "answer_count": target.get("answer_count", 0),
                            "follower_count": target.get("follower_count", 0),
                        },
                    }
                )
        except Exception as e:
            logger.error(f"[zhihu] Parse failed: {e}")
            return []

        return results
