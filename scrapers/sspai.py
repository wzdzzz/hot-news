"""少数派热榜爬虫"""
from __future__ import annotations

import logging

import httpx

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class SspaiScraper(BaseScraper):
    source = "sspai"
    category = "media"
    base_url = "https://sspai.com"

    async def fetch(self, client: httpx.AsyncClient) -> list[dict]:
        api = (
            "https://sspai.com/api/v1/article/index/page/get"
            "?limit=20&offset=0&created_at=0&sort=hot&include_total=false"
        )
        try:
            resp = await client.get(api)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"[sspai] Request failed: {e}")
            return []

        results: list[dict] = []
        try:
            articles = data.get("data", []) or []
            for idx, item in enumerate(articles, start=1):
                title = item.get("title", "")
                article_id = item.get("id", "")
                url = f"https://sspai.com/post/{article_id}" if article_id else ""
                summary = item.get("summary", "")
                image_url = item.get("banner", "") or item.get("cover", "")
                if image_url and not image_url.startswith("http"):
                    image_url = f"https://cdn.sspai.com/{image_url}"
                hot_value = item.get("like_count", 0) or item.get("likes_count", 0)
                comment_count = item.get("comment_count", 0)
                author_info = item.get("author", {}) or {}
                author = author_info.get("nickname", "") if isinstance(author_info, dict) else ""

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
                            "article_id": str(article_id),
                            "author": author,
                            "comment_count": comment_count,
                        },
                    }
                )
        except Exception as e:
            logger.error(f"[sspai] Parse failed: {e}")
            return []

        return results
