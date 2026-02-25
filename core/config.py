import os
from pathlib import Path
from typing import Any

import yaml

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 默认配置文件路径
DEFAULT_CONFIG_PATH = BASE_DIR / "config.yaml"


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """加载 YAML 配置文件"""
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# 全局配置单例
_config: dict[str, Any] | None = None


def get_config() -> dict[str, Any]:
    """获取全局配置（懒加载）"""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def get_scraper_config(name: str) -> dict[str, Any]:
    """获取指定爬虫的配置"""
    cfg = get_config()
    scrapers = cfg.get("scrapers", {})
    return scrapers.get(name, {"enabled": False, "interval": 7200, "max_items": 30})


def get_database_path() -> str:
    """获取数据库文件路径（绝对路径）"""
    cfg = get_config()
    db_path = cfg.get("database", {}).get("path", "./data/hot_news.db")
    full_path = BASE_DIR / db_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    return str(full_path)
