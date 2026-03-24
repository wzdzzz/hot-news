"""36氪热榜爬虫"""
from __future__ import annotations

import json
import logging

import httpx

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class Kr36Scraper(BaseScraper):
    source = "kr36"
    category = "media"
    base_url = "https://36kr.com"

    async def fetch(self, client: httpx.AsyncClient) -> list[dict]:
        api = "https://gateway.36kr.com/api/mis/nav/home/nav/rank/hot"
        payload = {
            "partner_id": "wap",
            "timestamp": "",
            "param": {
                "siteId": 1,
                "platformId": 2,
            },
        }
        try:
            resp = await client.post(api, json=payload)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"[kr36] Request failed: {e}")
            return []

        results: list[dict] = []
        try:
            inner = data.get("data", {})
            # API 有时返回 JSON 字符串，有时返回 dict
            if isinstance(inner, str):
                inner = json.loads(inner)
            hot_list = (
                inner.get("hotRankList", [])
                or inner.get("itemList", [])
                or []
            )
            for idx, item in enumerate(hot_list, start=1):
                template_material = item.get("templateMaterial", {}) or {}
                widget_title = template_material.get("widgetTitle", "")
                widget_image = template_material.get("widgetImage", "")
                widget_summary = template_material.get("widgetSummary", "")

                # widgetTitle/widgetImage 可能是 str 或 dict
                if isinstance(widget_title, dict):
                    title = widget_title.get("title", "")
                else:
                    title = widget_title or ""
                title = title or item.get("title", "") or item.get("templateTitle", "")

                item_id = (
                    template_material.get("itemId", "")
                    or item.get("itemId", "")
                    or item.get("id", "")
                )
                url = f"https://36kr.com/p/{item_id}" if item_id else ""
                hot_value = item.get("hotRank", 0) or item.get("hot", 0)

                if isinstance(widget_summary, dict):
                    summary = widget_summary.get("summary", "")
                else:
                    summary = widget_summary or ""
                summary = summary or item.get("summary", "")

                if isinstance(widget_image, dict):
                    image_url = widget_image.get("image", "")
                else:
                    image_url = widget_image or ""
                image_url = image_url or item.get("cover", "")

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
                            "item_id": str(item_id),
                            "author": item.get("authorName", ""),
                        },
                    }
                )
        except Exception as e:
            logger.error(f"[kr36] Parse failed: {e}")
            return []

        return results
