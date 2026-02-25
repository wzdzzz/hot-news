"""CNN 新闻爬虫"""

import logging

import httpx
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class CNNScraper(BaseScraper):
    source = "cnn"
    category = "news"
    base_url = "https://edition.cnn.com"

    async def fetch(self, client: httpx.AsyncClient) -> list[dict]:
        # Try lite.cnn.com first (simpler HTML, more reliable parsing)
        results = await self._fetch_lite(client)
        if results:
            return results

        # Fallback to main edition.cnn.com
        return await self._fetch_main(client)

    async def _fetch_lite(self, client: httpx.AsyncClient) -> list[dict]:
        """Fetch from lite.cnn.com - cleaner HTML structure."""
        try:
            resp = await client.get("https://lite.cnn.com/")
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            logger.warning(f"[cnn] lite.cnn.com request failed: {e}")
            return []

        results: list[dict] = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            seen_titles: set[str] = set()

            # lite.cnn.com has a simple list of <a> tags with headlines
            for a_tag in soup.select("ul li a, ol li a, a.container__link"):
                title = a_tag.get_text(strip=True)
                if not title or title in seen_titles:
                    continue
                # Skip navigation / non-article links
                if len(title) < 10:
                    continue
                seen_titles.add(title)

                href = a_tag.get("href", "")
                if href.startswith("/"):
                    href = f"https://www.cnn.com{href}"

                results.append(
                    {
                        "title": title,
                        "url": href,
                        "hot_value": 0,
                        "rank": len(results) + 1,
                        "summary": "",
                        "image_url": "",
                        "extra": {"source_page": "lite"},
                    }
                )
        except Exception as e:
            logger.error(f"[cnn] lite parse failed: {e}")
            return []

        return results

    async def _fetch_main(self, client: httpx.AsyncClient) -> list[dict]:
        """Fetch from edition.cnn.com - full site with richer data."""
        try:
            resp = await client.get(self.base_url)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            logger.error(f"[cnn] edition.cnn.com request failed: {e}")
            return []

        results: list[dict] = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            seen_titles: set[str] = set()

            # CNN uses various container classes for headlines
            headline_selectors = (
                'span[data-editable="headline"], '
                'span.container__headline-text, '
                "h3.cd__headline, "
                'a[data-link-type="article"] span'
            )
            for tag in soup.select(headline_selectors):
                title = tag.get_text(strip=True)
                if not title or title in seen_titles:
                    continue
                if len(title) < 10:
                    continue
                seen_titles.add(title)

                link_tag = tag.find_parent("a")
                href = ""
                if link_tag and link_tag.get("href"):
                    href = link_tag["href"]
                    if href.startswith("/"):
                        href = f"https://www.cnn.com{href}"

                image_url = ""
                parent = tag.find_parent("div")
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
                        "summary": "",
                        "image_url": image_url,
                        "extra": {"source_page": "main"},
                    }
                )

            # Broader fallback: look for any <a> containing headlines
            if not results:
                for a_tag in soup.find_all("a", href=True):
                    span = a_tag.find("span")
                    if not span:
                        continue
                    title = span.get_text(strip=True)
                    if not title or len(title) < 15 or title in seen_titles:
                        continue
                    seen_titles.add(title)
                    href = a_tag["href"]
                    if href.startswith("/"):
                        href = f"https://www.cnn.com{href}"
                    results.append(
                        {
                            "title": title,
                            "url": href,
                            "hot_value": 0,
                            "rank": len(results) + 1,
                            "summary": "",
                            "image_url": "",
                            "extra": {"source_page": "main"},
                        }
                    )

        except Exception as e:
            logger.error(f"[cnn] main parse failed: {e}")
            return []

        return results
