import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.hot import router as hot_router
from api.routes.scraper import router as scraper_router
from core.config import get_config
from core.scheduler import scheduler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/app.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化调度器，关闭时清理"""
    logger.info("Starting Hot News Scraper...")
    scheduler.setup()
    scheduler.start()
    logger.info("Scheduler started, API ready")
    yield
    scheduler.shutdown()
    logger.info("Shutdown complete")


app = FastAPI(
    title="Hot News Scraper API",
    description="热点新闻聚合爬虫系统 API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置
config = get_config()
cors_origins = config.get("api", {}).get("cors_origins", ["http://localhost:5173"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(hot_router)
app.include_router(scraper_router)


@app.get("/")
async def root():
    return {"message": "Hot News Scraper API is running", "docs": "/docs"}
