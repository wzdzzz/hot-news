from __future__ import annotations

from scrapers.weibo import WeiboScraper
from scrapers.baidu import BaiduScraper
from scrapers.zhihu import ZhihuScraper
from scrapers.sina_news import SinaNewsScraper
from scrapers.netease import NeteaseScraper
from scrapers.bbc import BBCScraper
from scrapers.cnn import CNNScraper
from scrapers.reuters import ReutersScraper
from scrapers.juejin import JuejinScraper
from scrapers.csdn import CSDNScraper
from scrapers.github_trending import GitHubTrendingScraper
from scrapers.hackernews import HackerNewsScraper
from scrapers.douyin import DouyinScraper
from scrapers.bilibili import BilibiliScraper
from scrapers.toutiao import ToutiaoScraper
from scrapers.kr36 import Kr36Scraper
from scrapers.huxiu import HuxiuScraper
from scrapers.sspai import SspaiScraper

SCRAPER_MAP: dict[str, type] = {
    "weibo": WeiboScraper,
    "baidu": BaiduScraper,
    "zhihu": ZhihuScraper,
    "sina_news": SinaNewsScraper,
    "netease": NeteaseScraper,
    "bbc": BBCScraper,
    "cnn": CNNScraper,
    "reuters": ReutersScraper,
    "juejin": JuejinScraper,
    "csdn": CSDNScraper,
    "github_trending": GitHubTrendingScraper,
    "hackernews": HackerNewsScraper,
    "douyin": DouyinScraper,
    "bilibili": BilibiliScraper,
    "toutiao": ToutiaoScraper,
    "kr36": Kr36Scraper,
    "huxiu": HuxiuScraper,
    "sspai": SspaiScraper,
}


def get_scraper(name: str):
    """根据名称获取爬虫实例"""
    cls = SCRAPER_MAP.get(name)
    if cls is None:
        raise ValueError(f"Unknown scraper: {name}")
    return cls()
