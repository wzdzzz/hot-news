"""Hacker News 爬虫"""
from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Optional

import httpx

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

HN_API_BASE = "https://hacker-news.firebaseio.com/v0"


class HackerNewsScraper(BaseScraper):
    source = "hackernews"
    category = "tech"
    base_url = "https://news.ycombinator.com"

    async def fetch(self, client: httpx.AsyncClient) -> List[dict]:
        # Step 1: Get top story IDs
        try:
            resp = await client.get(f"{HN_API_BASE}/topstories.json")
            resp.raise_for_status()
            story_ids: List[int] = resp.json()
        except Exception as e:
            logger.error(f"[hackernews] Failed to fetch top stories: {e}")
            return []

        if not isinstance(story_ids, list):
            logger.error("[hackernews] Unexpected response format for top stories")
            return []

        # Limit to max_items to avoid excessive requests
        story_ids = story_ids[: self.max_items]

        # Step 2: Fetch each story item concurrently
        async def fetch_item(item_id: int) -> Optional[dict]:
            try:
                r = await client.get(f"{HN_API_BASE}/item/{item_id}.json")
                r.raise_for_status()
                return r.json()
            except Exception as e:
                logger.debug(f"[hackernews] Failed to fetch item {item_id}: {e}")
                return None

        # Use semaphore to limit concurrent requests
        sem = asyncio.Semaphore(10)

        async def fetch_with_sem(item_id: int) -> Optional[dict]:
            async with sem:
                return await fetch_item(item_id)

        tasks = [fetch_with_sem(sid) for sid in story_ids]
        raw_items = await asyncio.gather(*tasks)

        # Step 3: Build results
        results: List[dict] = []
        for rank, item_data in enumerate(raw_items, start=1):
            if item_data is None:
                continue
            if item_data.get("type") != "story":
                continue

            title = item_data.get("title", "")
            if not title:
                continue

            url = item_data.get("url", "")
            item_id = item_data.get("id", 0)
            # If no external URL, link to the HN discussion page
            if not url:
                url = f"https://news.ycombinator.com/item?id={item_id}"

            score = item_data.get("score", 0)
            author = item_data.get("by", "")
            descendants = item_data.get("descendants", 0)
            text = item_data.get("text", "")

            results.append(
                {
                    "title": title,
                    "url": url,
                    "hot_value": score,
                    "rank": rank,
                    "summary": text[:300] if text else "",
                    "image_url": "",
                    "extra": {
                        "author": author,
                        "comments": descendants,
                        "hn_url": f"https://news.ycombinator.com/item?id={item_id}",
                        "item_id": item_id,
                    },
                }
            )

        return results
