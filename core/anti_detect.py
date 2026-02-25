import asyncio
import random
import time
import logging
from collections import defaultdict

from core.config import get_config

logger = logging.getLogger(__name__)

# 常用 User-Agent 列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
]

# 令牌桶 - 每个来源独立限速
_token_buckets: dict[str, float] = defaultdict(lambda: time.time())


def get_random_ua() -> str:
    """随机获取一个 User-Agent"""
    return random.choice(USER_AGENTS)


def get_headers(referer: str = "") -> dict[str, str]:
    """生成完整的伪装请求头"""
    headers = {
        "User-Agent": get_random_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
    }
    if referer:
        headers["Referer"] = referer
    return headers


async def random_delay(source: str = ""):
    """随机延迟，避免请求过于频繁"""
    cfg = get_config().get("anti_detect", {})
    min_delay = cfg.get("min_delay", 2)
    max_delay = cfg.get("max_delay", 8)
    delay = random.uniform(min_delay, max_delay)
    logger.debug(f"[{source}] Delaying {delay:.1f}s")
    await asyncio.sleep(delay)


async def rate_limit_wait(source: str):
    """令牌桶限速：确保同一来源的请求间隔足够"""
    cfg = get_config().get("anti_detect", {})
    rate = cfg.get("rate_limit", 10)  # 每分钟最大请求数
    interval = 60.0 / rate

    last_request = _token_buckets[source]
    now = time.time()
    wait_time = interval - (now - last_request)

    if wait_time > 0:
        logger.debug(f"[{source}] Rate limit wait {wait_time:.1f}s")
        await asyncio.sleep(wait_time)

    _token_buckets[source] = time.time()
