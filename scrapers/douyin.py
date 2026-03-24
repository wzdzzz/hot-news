"""抖音热榜爬虫"""
from __future__ import annotations
from typing import List

import logging

import httpx

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class DouyinScraper(BaseScraper):
    source = "douyin"
    category = "social"
    base_url = "https://www.douyin.com"

    async def fetch(self, client: httpx.AsyncClient) -> List[dict]:
        api = "https://www.douyin.com/aweme/v1/web/hot/search/list/"
        try:
            resp = await client.get(api)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"[douyin] Request failed: {e}")
            return []

        results: List[dict] = []
        try:
            word_list = data.get("data", {}).get("word_list", [])

            for idx, item in enumerate(word_list, start=1):
                word = item.get("word", "")
                hot_value = item.get("hot_value", 0)
                sentence_id = item.get("sentence_id", "")
                event_time = item.get("event_time", "")
                cover = item.get("word_cover", {})
                image_url = ""
                if isinstance(cover, dict):
                    url_list = cover.get("url_list", [])
                    if url_list:
                        image_url = url_list[0]

                search_url = f"https://www.douyin.com/search/{word}" if word else ""

                results.append(
                    {
                        "title": word,
                        "url": search_url,
                        "hot_value": hot_value,
                        "rank": idx,
                        "summary": "",
                        "image_url": image_url,
                        "extra": {
                            "sentence_id": sentence_id,
                            "event_time": event_time,
                            "label": item.get("label", 0),
                        },
                    }
                )
        except Exception as e:
            logger.error(f"[douyin] Parse failed: {e}")
            return []

        return results
