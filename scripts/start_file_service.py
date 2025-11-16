#!/usr/bin/env python3
"""
文件服务启动脚本
"""
import os
import sys
import uvicorn
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def main():
    """启动文件服务"""
    
    # 设置环境变量
    os.environ.setdefault("FILE_LOCAL_BASE_PATH", "./uploads")
    os.environ.setdefault("FILE_LOCAL_BASE_URL", "http://localhost:8001/api/v1/files/static")
    os.environ.setdefault("FILE_MAX_SIZE", str(10 * 1024 * 1024))  # 10MB
    os.environ.setdefault("FILE_ALLOWED_EXTENSIONS", ".jpg,.jpeg,.png,.gif,.pdf,.doc,.docx,.txt,.zip,.mp4,.mp3")
    
    # 创建上传目录
    upload_dir = Path("./uploads")
    upload_dir.mkdir(exist_ok=True)
    
    thumbnail_dir = Path("./thumbnails")
    thumbnail_dir.mkdir(exist_ok=True)
    
    print("🚀 启动文件服务...")
    print(f"📁 上传目录: {upload_dir.absolute()}")
    print(f"🖼️  缩略图目录: {thumbnail_dir.absolute()}")
    print("🌐 API文档: http://localhost:8001/docs")
    print("📋 文件管理: http://localhost:8001/api/v1/files/")
    
    # 启动服务
    uvicorn.run(
        "api_gateway.app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()