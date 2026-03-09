"""BBC News 爬虫"""

import logging

import httpx
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class BBCScraper(BaseScraper):
    source = "bbc"
    category = "news"
    base_url = "https://www.bbc.com/news"

    @staticmethod
    async def fetch_article_content(url: str) -> dict:
        """抓取 BBC 文章正文内容，返回 {title, content, author, published_time}"""
        from core.anti_detect import get_headers

        headers = get_headers(referer="https://www.bbc.com/news")
        async with httpx.AsyncClient(
            headers=headers, timeout=30, follow_redirects=True
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # 提取标题
        title = ""
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)

        # 提取正文段落 - BBC 文章正文通常在 article 标签内的 p 标签
        paragraphs: list[str] = []
        article = soup.find("article")
        if article:
            for p in article.find_all("p"):
                text = p.get_text(strip=True)
                # 过滤掉太短的段落（通常是标签或注释）
                if text and len(text) > 10:
                    paragraphs.append(text)
        else:
            # 备用：查找主要内容区域
            for selector in [
                '[data-component="text-block"]',
                ".ssrcss-uf6wea-RichTextComponentWrapper",
                'div[class*="TextContainerWrapper"]',
            ]:
                blocks = soup.select(selector)
                if blocks:
                    for block in blocks:
                        text = block.get_text(strip=True)
                        if text and len(text) > 10:
                            paragraphs.append(text)
                    break

        content = "\n\n".join(paragraphs)

        # 提取作者
        author = ""
        author_tag = soup.select_one(
            '[data-testid="byline"], .ssrcss-68pt20-Text-TextContributorName'
        )
        if author_tag:
            author = author_tag.get_text(strip=True)

        # 提取发布时间
        published_time = ""
        time_tag = soup.find("time")
        if time_tag:
            published_time = time_tag.get("datetime", "") or time_tag.get_text(strip=True)

        return {
            "title": title,
            "content": content,
            "author": author,
            "published_time": published_time,
        }

    async def fetch(self, client: httpx.AsyncClient) -> list[dict]:
        try:
            resp = await client.get(self.base_url)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            logger.error(f"[bbc] Request failed: {e}")
            return []

        results: list[dict] = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            seen_titles: set[str] = set()

            # BBC uses data-testid attributes and <h2> tags for headlines
            headline_tags = soup.select(
                '[data-testid="card-headline"], '
                'h2[data-testid="card-headline"], '
                "article h2, "
                'div[class*="PromoHeadline"] h3, '
                'div[class*="Media"] h3'
            )

            for tag in headline_tags:
                title = tag.get_text(strip=True)
                if not title or title in seen_titles:
                    continue
                seen_titles.add(title)

                # Walk up to find the enclosing <a> tag for the link
                link_tag = tag.find_parent("a")
                if link_tag is None:
                    link_tag = tag.find("a")
                href = ""
                if link_tag and link_tag.get("href"):
                    href = link_tag["href"]
                    if href.startswith("/"):
                        href = f"https://www.bbc.com{href}"

                # Try to find a sibling summary / description
                summary = ""
                desc_tag = tag.find_next_sibling("p")
                if desc_tag:
                    summary = desc_tag.get_text(strip=True)

                # Try to find an associated image
                image_url = ""
                parent_article = tag.find_parent("article") or tag.find_parent("div")
                if parent_article:
                    img_tag = parent_article.find("img")
                    if img_tag:
                        image_url = img_tag.get("src", "") or img_tag.get("data-src", "")

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

            # Fallback: if no headlines found via selectors, try all <h3> inside links
            if not results:
                for a_tag in soup.find_all("a", href=True):
                    h3 = a_tag.find("h3")
                    if not h3:
                        continue
                    title = h3.get_text(strip=True)
                    if not title or title in seen_titles:
                        continue
                    seen_titles.add(title)
                    href = a_tag["href"]
                    if href.startswith("/"):
                        href = f"https://www.bbc.com{href}"
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
            logger.error(f"[bbc] Parse failed: {e}")
            return []

        return results
