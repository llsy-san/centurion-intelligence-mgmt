"""
文件服务配置
"""
import os
from typing import Optional

from ..file_models import (
    FileServiceConfig, LocalStorageConfig, OSSConfig, 
    UploadConfig, StorageType
)


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