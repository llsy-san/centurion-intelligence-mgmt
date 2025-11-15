"""
支付服务主应用
负责处理支付相关的业务逻辑
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
import sys
import os

# 添加共享模块到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))

from .models import Payment, PaymentCreate, PaymentStatus, BaseResponse
from config import PaymentServiceConfig
from utils import setup_logging, format_response

from .database import get_db, init_db
from .routers import payments

# 初始化配置和日志
config = PaymentServiceConfig()
logger = setup_logging("payment-service")

# 创建FastAPI应用
app = FastAPI(
    title="支付服务",
    description="处理支付相关的业务逻辑",
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
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("支付服务启动中...")
    await init_db()
    logger.info("支付服务启动完成")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("支付服务关闭中...")


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return format_response(message="支付服务运行正常")


@app.get("/")
async def root():
    """根路径"""
    return format_response(message="欢迎使用支付服务API")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="info"
    )