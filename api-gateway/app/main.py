"""
API网关主应用
负责统一对外提供接口，路由转发和鉴权
"""
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any
import httpx

from .config import config
from .utils import setup_logging, format_response
from .middleware import LoggingMiddleware
from .routers import gateway, files, orders, payments, shipping

# 初始化日志
logger = setup_logging(config.log_level, config.log_format)

# 创建FastAPI应用
app = FastAPI(
    title="百夫长智能管理系统API网关",
    description="统一对外提供接口，负责路由转发和鉴权",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 注册路由
app.include_router(gateway.router, prefix="/api/v1", tags=["认证"])
app.include_router(files.router, tags=["文件管理"])
app.include_router(orders.router, prefix="/api/v1", tags=["订单管理"])
app.include_router(payments.router, prefix="/api/v1", tags=["支付管理"])
app.include_router(shipping.router, prefix="/api/v1", tags=["发货管理"])

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加自定义中间件
app.add_middleware(LoggingMiddleware)

# 安全认证
security = HTTPBearer()


# 健康检查和基础路由将在下面定义
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """获取当前用户（JWT认证）"""
    # 暂时跳过JWT验证，返回模拟用户
    return {"user_id": "test", "username": "test_user"}


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("API网关启动中...")
    logger.info("API网关启动完成")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("API网关关闭中...")


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return format_response(message="API网关运行正常")


@app.get("/")
async def root():
    """根路径"""
    return format_response(message="欢迎使用百夫长智能管理系统API")


# 注意：原来的通配符代理路由已被具体的路由替换
# 如果需要处理未定义的路由，可以保留一个通用的代理处理器


async def proxy_request(request: Request, service_url: str, path: str):
    """代理请求到后端服务"""
    try:
        # 获取请求体
        body = await request.body()

        # 构建目标URL
        target_url = f"{service_url}{path}"

        # 获取查询参数
        query_params = dict(request.query_params)

        # 获取请求头（排除一些不需要的头）
        headers = dict(request.headers)
        excluded_headers = ['host', 'content-length', 'authorization']
        headers = {k: v for k, v in headers.items() if k.lower() not in excluded_headers}

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                params=query_params,
                headers=headers,
                content=body,
                timeout=30.0
            )

            # 返回响应
            return response.json() if response.headers.get('content-type', '').startswith(
                'application/json') else response.text

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="服务请求超时"
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="服务不可用"
        )
    except Exception as e:
        logger.error(f"代理请求失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="内部服务错误"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="info"
    )
