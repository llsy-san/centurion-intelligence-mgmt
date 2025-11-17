from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 创建FastAPI应用
app = FastAPI(
    title="AI智能体服务",
    description="百夫长智能管理系统 - AI智能体服务API",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查端点
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ai-agent-service",
        "version": "1.0.0"
    }

# 根路径
@app.get("/")
async def root():
    return {"message": "AI智能体服务运行中"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)