"""
定时任务服务主应用
负责从第三方系统获取订单数据并同步到本地数据库
"""
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import config
from .utils import setup_logging, format_response

from .database import init_db
from .routers.tasks import router as tasks_router
from .routers.sync import router as sync_router
from .scheduler import start_scheduler, stop_scheduler

# 初始化配置和日志
# config 已经是实例，无需再次实例化
logger = setup_logging("task-scheduler-service")


@asynccontextmanager
async def lifespan(app):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("定时任务服务启动中...")
    await init_db()
    await start_scheduler()
    logger.info("定时任务服务启动完成")
    
    yield
    
    # 关闭时执行
    logger.info("定时任务服务关闭中...")
    await stop_scheduler()
    logger.info("定时任务服务关闭完成")


# 创建FastAPI应用
app = FastAPI(
    title="百夫长智能管理系统 - 定时任务服务",
    description="Centurion Intelligence Management System - 处理第三方数据同步和定时任务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(tasks_router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(sync_router, prefix="/api/v1/sync", tags=["sync"])

# 导入并包含 Celery 任务管理路由
from .routers.celery_jobs import router as celery_router
app.include_router(celery_router, prefix="/api/v1/celery", tags=["celery-jobs"])


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return format_response(message="百夫长智能管理系统定时任务服务运行正常")


@app.get("/")
async def root():
    """根路径"""
    return format_response(message="欢迎使用百夫长智能管理系统定时任务服务API")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="info"
    )