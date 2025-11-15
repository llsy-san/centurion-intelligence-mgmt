"""
订单服务主应用
负责处理订单的创建、查询、更新等业务逻辑
"""
import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))

from config import OrderServiceConfig
from utils import setup_logging, format_response

from .database import init_db
from .routers import orders, query

# 初始化配置和日志
config = OrderServiceConfig()
logger = setup_logging("order-service")

# 创建FastAPI应用
app = FastAPI(
    title="订单服务",
    description="处理订单相关的业务逻辑",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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
app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])
app.include_router(query.router, prefix="/api/v1/query", tags=["query"])


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("订单服务启动中...")
    await init_db()
    logger.info("订单服务启动完成")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("订单服务关闭中...")


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return format_response(message="订单服务运行正常")


@app.get("/")
async def root():
    """根路径"""
    return format_response(message="欢迎使用订单服务API")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="info"
    )