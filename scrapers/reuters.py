"""Reuters 新闻爬虫"""
from __future__ import annotations
from typing import List

import logging

import httpx
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class ReutersScraper(BaseScraper):
    source = "reuters"
    category = "news"
    base_url = "https://www.reuters.com"

    async def fetch(self, client: httpx.AsyncClient) -> List[dict]:
        try:
            resp = await client.get(self.base_url)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            logger.error(f"[reuters] Request failed: {e}")
            return []

        results: List[dict] = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            seen_titles: set = set()

            # Reuters uses data-testid attributes for headlines
            headline_selectors = (
                '[data-testid="Heading"] a, '
                '[data-testid="TitleHeading"], '
                'h3[data-testid="Heading"], '
                "article h3, "
                'a[data-testid="Title"], '
                'div[class*="story-content"] h3'
            )
            for tag in soup.select(headline_selectors):
                title = tag.get_text(strip=True)
                if not title or title in seen_titles:
                    continue
                if len(title) < 8:
                    continue
                seen_titles.add(title)

                # Resolve the link
                href = ""
                if tag.name == "a":
                    href = tag.get("href", "")
                else:
                    link_tag = tag.find_parent("a") or tag.find("a")
                    if link_tag:
                        href = link_tag.get("href", "")
                if href.startswith("/"):
                    href = f"https://www.reuters.com{href}"

                # Try to grab a summary from a sibling <p>
                summary = ""
                p_tag = tag.find_next("p")
                if p_tag:
                    summary = p_tag.get_text(strip=True)
                    # Avoid grabbing unrelated long text
                    if len(summary) > 300:
                        summary = summary[:300]

                # Image
                image_url = ""
                parent = tag.find_parent("article") or tag.find_parent("div")
                if parent:
                    img = parent.find("img")
                    if img:
                        image_url = img.get("src", "") or img.get("data-src", "")

                results.append(
                    {
                        "title": title,
                        "url": href,
                        "hot_value": 0,
                        "rank": len(results) + 1,
                        "summary": summary,
                        "image_url": image_url,
                        "extra": {},
                    }
                )

            # Fallback: scan for <a> elements that contain article links
            if not results:
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"]
                    # Reuters article URLs typically match /world/... /business/... etc.
                    if not any(
                        seg in href
                        for seg in ("/world/", "/business/", "/markets/", "/technology/", "/sports/")
                    ):
                        continue
                    title = a_tag.get_text(strip=True)
                    if not title or len(title) < 15 or title in seen_titles:
                        continue
                    seen_titles.add(title)
                    if href.startswith("/"):
                        href = f"https://www.reuters.com{href}"
                    results.append(
                        {
                            "title": title,
                            "url": href,
                            "hot_value": 0,
                            "rank": len(results) + 1,
                            "summary": "",
                            "image_url": "",
                            "extra": {},
                        }
                    )

        except Exception as e:
            logger.error(f"[reuters] Parse failed: {e}")
            return []

        return results
