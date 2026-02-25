"""
Hot News Scraper 启动入口
同时启动 FastAPI 服务 + 定时爬虫调度器
"""

import sys
import os

# 将项目根目录加入 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from core.config import get_config


def main():
    config = get_config()
    api_config = config.get("api", {})
    host = api_config.get("host", "0.0.0.0")
    port = api_config.get("port", 8111)

    print(f"Starting Hot News Scraper...")
    print(f"   API: http://localhost:{port}")
    print(f"   Docs: http://localhost:{port}/docs")

    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()
