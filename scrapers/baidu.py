"""百度热搜爬虫"""
from __future__ import annotations

import logging

import httpx
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class BaiduScraper(BaseScraper):
    source = "baidu"
    category = "news"
    base_url = "https://top.baidu.com"

    async def fetch(self, client: httpx.AsyncClient) -> list[dict]:
        url = "https://top.baidu.com/board?tab=realtime"
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            logger.error(f"[baidu] Request failed: {e}")
            return []

        results: list[dict] = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select("div.category-wrap_iQLoo")

            for idx, card in enumerate(cards, start=1):
                # Title
                title_tag = card.select_one("div.c-single-text-ellipsis")
                title = title_tag.get_text(strip=True) if title_tag else ""

                # Hot value
                hot_tag = card.select_one("div.hot-index_1Bl1a")
                hot_value = hot_tag.get_text(strip=True) if hot_tag else "0"

                # Summary / description
                desc_tag = card.select_one("div.hot-desc_1m_jR")
                summary = desc_tag.get_text(strip=True) if desc_tag else ""

                # Link
                link_tag = card.select_one("a.title_dIF3B")
                if not link_tag:
                    link_tag = card.select_one("a")
                href = link_tag.get("href", "") if link_tag else ""

                # Image
                img_tag = card.select_one("img")
                image_url = img_tag.get("src", "") if img_tag else ""

                if not title:
                    continue

                results.append(
                    {
                        "title": title,
                        "url": href,
                        "hot_value": hot_value,
                        "rank": idx,
                        "summary": summary,
                        "image_url": image_url,
                        "extra": {},
                    }
                )
        except Exception as e:
            logger.error(f"[baidu] Parse failed: {e}")
            return []

        return results
