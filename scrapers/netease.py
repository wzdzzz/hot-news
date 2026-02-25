"""网易新闻热榜爬虫"""

import logging

import httpx

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class NeteaseScraper(BaseScraper):
    source = "netease"
    category = "news"
    base_url = "https://m.163.com"

    async def fetch(self, client: httpx.AsyncClient) -> list[dict]:
        api = "https://m.163.com/fe/api/hot/news/flow"
        try:
            resp = await client.get(api)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"[netease] Request failed: {e}")
            return []

        results: list[dict] = []
        try:
            # 网易热榜接口返回 data.data 列表
            items = data.get("data", {})
            if isinstance(items, dict):
                items = items.get("list", []) or items.get("items", [])
            if not isinstance(items, list):
                items = []

            for idx, item in enumerate(items, start=1):
                title = item.get("title", "")
                doc_id = item.get("docid", "") or item.get("id", "")
                url = item.get("url", "")
                if not url and doc_id:
                    url = f"https://www.163.com/dy/article/{doc_id}.html"
                hot_value = item.get("hotScore", 0) or item.get("votecount", 0)
                summary = item.get("digest", "") or item.get("summary", "")
                image_url = item.get("imgsrc", "") or item.get("image", "")
                source_name = item.get("source", "")

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
                            "source": source_name,
                            "docid": doc_id,
                            "comment_count": item.get("commentCount", 0),
                        },
                    }
                )
        except Exception as e:
            logger.error(f"[netease] Parse failed: {e}")
            return []

        return results
