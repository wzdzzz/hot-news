"""微博热搜爬虫"""
from __future__ import annotations
from typing import List

import logging

import httpx

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class WeiboScraper(BaseScraper):
    source = "weibo"
    category = "social"
    base_url = "https://weibo.com"

    async def fetch(self, client: httpx.AsyncClient) -> List[dict]:
        api = "https://weibo.com/ajax/side/hotSearch"
        try:
            resp = await client.get(api)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"[weibo] Request failed: {e}")
            return []

        results: List[dict] = []
        try:
            realtime = data.get("data", {}).get("realtime", [])
            for idx, item in enumerate(realtime, start=1):
                word = item.get("word", "")
                note = item.get("note", word)
                num = item.get("num", 0)
                label_name = item.get("label_name", "")
                icon_desc = item.get("icon_desc", "")

                results.append(
                    {
                        "title": note or word,
                        "url": f"https://s.weibo.com/weibo?q=%23{word}%23",
                        "hot_value": num,
                        "rank": idx,
                        "summary": "",
                        "image_url": "",
                        "extra": {
                            "label_name": label_name,
                            "icon_desc": icon_desc,
                            "word": word,
                        },
                    }
                )
        except Exception as e:
            logger.error(f"[weibo] Parse failed: {e}")
            return []

        return results
