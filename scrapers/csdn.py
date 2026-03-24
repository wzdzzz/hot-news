"""CSDN热榜爬虫"""
from __future__ import annotations
from typing import List

import logging

import httpx

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class CSDNScraper(BaseScraper):
    source = "csdn"
    category = "tech"
    base_url = "https://blog.csdn.net"

    async def fetch(self, client: httpx.AsyncClient) -> List[dict]:
        api = "https://blog.csdn.net/phoenix/web/blog/hot-rank?page=0&pageSize=25"
        try:
            resp = await client.get(api)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"[csdn] Request failed: {e}")
            return []

        results: List[dict] = []
        try:
            articles = data.get("data", []) or []
            for idx, item in enumerate(articles, start=1):
                title = item.get("articleTitle", "") or item.get("title", "")
                url = item.get("articleDetailUrl", "") or item.get("url", "")
                hot_value = item.get("hotRankScore", 0) or item.get("hotScore", 0)
                summary = item.get("articleDigest", "") or item.get("digest", "")
                image_url = item.get("pictureList", [""])[0] if item.get("pictureList") else ""
                author = item.get("nickName", "") or item.get("userName", "")
                comment_count = item.get("commentCount", 0)
                view_count = item.get("viewCount", 0)

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
                            "author": author,
                            "comment_count": comment_count,
                            "view_count": view_count,
                        },
                    }
                )
        except Exception as e:
            logger.error(f"[csdn] Parse failed: {e}")
            return []

        return results
