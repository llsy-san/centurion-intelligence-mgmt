import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from .models import (
    FileServiceConfig, LocalStorageConfig, OSSConfig,
    UploadConfig, StorageType
)


class GatewayConfig(BaseSettings):
    """API网关配置类"""
    
    # 应用基础设置
    app_name: str = "Centurion API Gateway"
    version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # 服务器设置
    host: str = "0.0.0.0"
    port: int = 8001
    
    # 数据库设置
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://postgres:centurion123@postgres:5432/centurion_db"
    )
    
    # Redis设置
    redis_url: str = os.getenv("REDIS_URL", "redis://:centurion123@redis:6379")
    
    # JWT设置
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    
    # CORS设置
    cors_origins: List[str] = ["*"]
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]
    
    # 文件存储设置
    upload_path: str = os.getenv("UPLOAD_PATH", "/app/uploads")
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: List[str] = ["image/jpeg", "image/png", "image/gif", "application/pdf"]
    
    # 外部服务URL
    order_service_url: str = os.getenv("ORDER_SERVICE_URL", "http://order-service:8002")
    payment_service_url: str = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8003")
    shipping_service_url: str = os.getenv("SHIPPING_SERVICE_URL", "http://shipping-service:8004")
    ai_agent_service_url: str = os.getenv("AI_AGENT_SERVICE_URL", "http://ai-agent-service:8005")
    task_scheduler_service_url: str = os.getenv("TASK_SCHEDULER_SERVICE_URL", "http://task-scheduler-service:8006")
    
    # OSS设置（阿里云对象存储）
    oss_access_key_id: Optional[str] = os.getenv("OSS_ACCESS_KEY_ID")
    oss_access_key_secret: Optional[str] = os.getenv("OSS_ACCESS_KEY_SECRET")
    oss_bucket_name: Optional[str] = os.getenv("OSS_BUCKET_NAME")
    oss_endpoint: Optional[str] = os.getenv("OSS_ENDPOINT")
    oss_region: Optional[str] = os.getenv("OSS_REGION", "oss-cn-hangzhou")
    
    # 日志设置
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 全局配置实例
config = GatewayConfig()

def get_file_service_config() -> FileServiceConfig:
    """获取文件服务配置"""

    # 本地存储配置
    local_config = LocalStorageConfig(
        base_path=os.getenv("FILE_LOCAL_BASE_PATH", "./uploads"),
        base_url=os.getenv("FILE_LOCAL_BASE_URL", "http://localhost:8001/files"),
        create_date_folder=os.getenv("FILE_CREATE_DATE_FOLDER", "true").lower() == "true",
        max_folder_files=int(os.getenv("FILE_MAX_FOLDER_FILES", "1000"))
    )

    # OSS配置（可选）
    oss_config = None
    if all([
        os.getenv("OSS_ACCESS_KEY_ID"),
        os.getenv("OSS_ACCESS_KEY_SECRET"),
        os.getenv("OSS_ENDPOINT"),
        os.getenv("OSS_BUCKET_NAME")
    ]):
        oss_config = OSSConfig(
            access_key_id=os.getenv("OSS_ACCESS_KEY_ID"),
            access_key_secret=os.getenv("OSS_ACCESS_KEY_SECRET"),
            endpoint=os.getenv("OSS_ENDPOINT"),
            bucket_name=os.getenv("OSS_BUCKET_NAME"),
            region=os.getenv("OSS_REGION"),
            custom_domain=os.getenv("OSS_CUSTOM_DOMAIN")
        )

    # 上传配置
    upload_config = UploadConfig(
        max_file_size=int(os.getenv("FILE_MAX_SIZE", str(10 * 1024 * 1024))),  # 默认10MB
        allowed_extensions=[
            ext.strip() for ext in
            os.getenv("FILE_ALLOWED_EXTENSIONS", ".jpg,.jpeg,.png,.gif,.pdf,.doc,.docx,.txt,.zip,.mp4,.mp3").split(",")
        ],
        upload_path=os.getenv("FILE_UPLOAD_PATH", "uploads")
    )

    # 默认存储类型
    default_storage = StorageType.LOCAL
    if os.getenv("FILE_DEFAULT_STORAGE", "local").lower() == "oss":
        default_storage = StorageType.OSS

    return FileServiceConfig(
        default_storage=default_storage,
        local_config=local_config,
        oss_config=oss_config,
        upload_config=upload_config,
        enable_thumbnail=os.getenv("FILE_ENABLE_THUMBNAIL", "true").lower() == "true",
        thumbnail_sizes=os.getenv("FILE_THUMBNAIL_SIZES", "150x150,300x300").split(",")
    )


# 全局配置实例
file_service_config = get_file_service_config()