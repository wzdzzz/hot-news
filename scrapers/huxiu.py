"""虎嗅热榜爬虫"""

import logging

import httpx

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class HuxiuScraper(BaseScraper):
    source = "huxiu"
    category = "media"
    base_url = "https://www.huxiu.com"

    async def fetch(self, client: httpx.AsyncClient) -> list[dict]:
        api = "https://api-article.huxiu.com/web/article/articleList"
        payload = {
            "platform": "www",
            "recommend_time": "0",
            "pagesize": str(self.max_items),
        }
        try:
            resp = await client.post(
                api,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"[huxiu] Request failed: {e}")
            return []

        results: list[dict] = []
        try:
            inner = data.get("data", {}) or {}
            articles = (
                inner.get("dataList", [])
                or inner.get("datalist", [])
                or inner.get("data", [])
                or []
            )
            for idx, item in enumerate(articles, start=1):
                title = item.get("title", "")
                aid = item.get("aid", "") or item.get("id", "")
                url = f"https://www.huxiu.com/article/{aid}.html" if aid else ""
                summary = item.get("summary", "") or item.get("description", "")
                image_url = item.get("pic_path", "") or item.get("cover", "")
                hot_value = (
                    item.get("count_info", {}).get("total_view", 0)
                    if isinstance(item.get("count_info"), dict)
                    else item.get("total_view", 0)
                )
                author = (
                    item.get("user_info", {}).get("username", "")
                    if isinstance(item.get("user_info"), dict)
                    else item.get("author_name", "")
                )
                comment_count = (
                    item.get("count_info", {}).get("comment", 0)
                    if isinstance(item.get("count_info"), dict)
                    else item.get("comment_count", 0)
                )

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
                            "aid": str(aid),
                            "author": author,
                            "comment_count": comment_count,
                        },
                    }
                )
        except Exception as e:
            logger.error(f"[huxiu] Parse failed: {e}")
            return []

        return results
