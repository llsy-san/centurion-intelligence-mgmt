"""
AI Agent服务主应用
提供智能客服、订单分析、风险评估等AI能力
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
import os

# 添加共享模块到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))

from .database import init_db
from .services import AIAgentService
from .routers import knowledge, vector_search, chat
from config import ServiceConfig

# 创建AI Agent服务配置
class AIAgentServiceConfig(ServiceConfig):
    service_name: str = "ai-agent-service"
    port: int = 8004

config = AIAgentServiceConfig()

# 创建FastAPI应用
app = FastAPI(
    title="AI Agent Service",
    description="智能客服和数据分析服务",
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
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["知识图谱"])
app.include_router(vector_search.router, prefix="/api/v1/vector", tags=["向量搜索"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["智能对话"])

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    await init_db()
    print(f"🤖 AI Agent服务启动成功，端口: {config.port}")

@app.get("/")
async def root():
    """根路径"""
    return {"message": "AI Agent Service", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "ai-agent-service"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.debug
    )