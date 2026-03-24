from __future__ import annotations

import logging
import random

import httpx

from core.config import get_config

logger = logging.getLogger(__name__)


class ProxyManager:
    """代理管理器（预留接口，默认关闭）"""

    def __init__(self):
        cfg = get_config().get("proxy", {})
        self.enabled = cfg.get("enabled", False)
        self.proxies: list[str] = cfg.get("proxies", [])
        self.api_url: str = cfg.get("api_url", "")

    def get_proxy(self) -> str | None:
        """获取一个可用代理，未启用则返回 None"""
        if not self.enabled:
            return None
        if not self.proxies:
            return None
        return random.choice(self.proxies)

    async def fetch_proxies_from_api(self):
        """从代理池 API 获取代理列表（需要时接入）"""
        if not self.api_url:
            return
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(self.api_url, timeout=10)
                if resp.status_code == 200:
                    # 根据实际 API 返回格式解析
                    data = resp.json()
                    self.proxies = data if isinstance(data, list) else []
                    logger.info(f"Fetched {len(self.proxies)} proxies from API")
        except Exception as e:
            logger.error(f"Failed to fetch proxies: {e}")

    async def check_proxy(self, proxy: str) -> bool:
        """验证代理是否可用"""
        try:
            async with httpx.AsyncClient(proxy=proxy, timeout=10) as client:
                resp = await client.get("https://httpbin.org/ip")
                return resp.status_code == 200
        except Exception:
            return False


# 全局代理管理器
proxy_manager = ProxyManager()
