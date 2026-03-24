"""GitHub Trending 爬虫"""
from __future__ import annotations
from typing import List

import logging

import httpx
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class GitHubTrendingScraper(BaseScraper):
    source = "github_trending"
    category = "tech"
    base_url = "https://github.com"

    async def fetch(self, client: httpx.AsyncClient) -> List[dict]:
        url = "https://github.com/trending"
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            logger.error(f"[github_trending] Request failed: {e}")
            return []

        results: List[dict] = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            rows = soup.select("article.Box-row")

            for idx, row in enumerate(rows, start=1):
                # Repo name (owner/repo)
                h2 = row.select_one("h2 a")
                if not h2:
                    continue
                repo_path = h2.get("href", "").strip("/")
                title = repo_path.replace("/", " / ")
                repo_url = f"https://github.com/{repo_path}"

                # Description
                p = row.select_one("p")
                summary = p.get_text(strip=True) if p else ""

                # Stars today
                stars_today = ""
                star_spans = row.select("span.d-inline-block.float-sm-right")
                if star_spans:
                    stars_today = star_spans[0].get_text(strip=True)

                # Total stars and forks
                links = row.select("a.Link--muted.d-inline-block.mr-3")
                total_stars = ""
                forks = ""
                if len(links) >= 1:
                    total_stars = links[0].get_text(strip=True)
                if len(links) >= 2:
                    forks = links[1].get_text(strip=True)

                # Language
                lang_span = row.select_one("span[itemprop='programmingLanguage']")
                language = lang_span.get_text(strip=True) if lang_span else ""

                results.append(
                    {
                        "title": title,
                        "url": repo_url,
                        "hot_value": stars_today or total_stars,
                        "rank": idx,
                        "summary": summary,
                        "image_url": "",
                        "extra": {
                            "total_stars": total_stars,
                            "forks": forks,
                            "language": language,
                            "stars_today": stars_today,
                        },
                    }
                )
        except Exception as e:
            logger.error(f"[github_trending] Parse failed: {e}")
            return []

        return results
