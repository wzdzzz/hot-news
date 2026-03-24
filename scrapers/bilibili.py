"""B站热门视频爬虫"""
from __future__ import annotations
from typing import List

import logging

import httpx

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class BilibiliScraper(BaseScraper):
    source = "bilibili"
    category = "social"
    base_url = "https://www.bilibili.com"

    async def fetch(self, client: httpx.AsyncClient) -> List[dict]:
        api = "https://api.bilibili.com/x/web-interface/ranking/v2"
        params = {"rid": 0, "type": "all"}
        try:
            resp = await client.get(api, params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"[bilibili] Request failed: {e}")
            return []

        results: List[dict] = []
        try:
            video_list = data.get("data", {}).get("list", [])

            for idx, item in enumerate(video_list, start=1):
                title = item.get("title", "")
                bvid = item.get("bvid", "")
                short_link = item.get("short_link_v2", "")
                url = short_link or f"https://www.bilibili.com/video/{bvid}"

                stat = item.get("stat", {})
                view = stat.get("view", 0)
                like = stat.get("like", 0)
                coin = stat.get("coin", 0)
                share = stat.get("share", 0)

                # Score used for ranking: use the stat.score or view count
                score = item.get("score", view)

                desc = item.get("desc", "")
                pic = item.get("pic", "")
                # Ensure https
                if pic and pic.startswith("//"):
                    pic = "https:" + pic

                owner = item.get("owner", {})

                results.append(
                    {
                        "title": title,
                        "url": url,
                        "hot_value": score,
                        "rank": idx,
                        "summary": desc,
                        "image_url": pic,
                        "extra": {
                            "bvid": bvid,
                            "view": view,
                            "like": like,
                            "coin": coin,
                            "share": share,
                            "author": owner.get("name", ""),
                            "author_mid": owner.get("mid", 0),
                            "duration": item.get("duration", 0),
                        },
                    }
                )
        except Exception as e:
            logger.error(f"[bilibili] Parse failed: {e}")
            return []

        return results
