"""
文件服务数据模型
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class StorageType(str, Enum):
    """存储类型"""
    LOCAL = "local"      # 本地文件服务器
    OSS = "oss"         # 阿里云OSS


class FileCategory(str, Enum):
    """文件分类"""
    IMAGE = "image"      # 图片
    DOCUMENT = "document" # 文档
    VIDEO = "video"      # 视频
    AUDIO = "audio"      # 音频
    OTHER = "other"      # 其他


class UploadConfig(BaseModel):
    """上传配置"""
    storage_type: StorageType = StorageType.LOCAL
    max_file_size: int = Field(default=10 * 1024 * 1024, description="最大文件大小(字节)")
    allowed_extensions: List[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx", ".txt"],
        description="允许的文件扩展名"
    )
    upload_path: Optional[str] = Field(default="uploads", description="上传路径")


class FileUploadRequest(BaseModel):
    """文件上传请求"""
    storage_type: StorageType = StorageType.LOCAL
    category: FileCategory = FileCategory.OTHER
    folder: Optional[str] = Field(default="", description="文件夹路径")
    custom_name: Optional[str] = Field(default=None, description="自定义文件名")
    overwrite: bool = Field(default=False, description="是否覆盖同名文件")


class FileInfo(BaseModel):
    """文件信息"""
    file_id: str = Field(..., description="文件ID")
    original_name: str = Field(..., description="原始文件名")
    file_name: str = Field(..., description="存储文件名")
    file_path: str = Field(..., description="文件路径")
    file_url: str = Field(..., description="访问URL")
    file_size: int = Field(..., description="文件大小(字节)")
    content_type: str = Field(..., description="文件类型")
    category: FileCategory = Field(..., description="文件分类")
    storage_type: StorageType = Field(..., description="存储类型")
    upload_time: datetime = Field(..., description="上传时间")
    uploader: Optional[str] = Field(default=None, description="上传者")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="文件元数据")


class FileListRequest(BaseModel):
    """文件列表请求"""
    category: Optional[FileCategory] = None
    storage_type: Optional[StorageType] = None
    folder: Optional[str] = None
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
    keyword: Optional[str] = Field(default=None, description="搜索关键词")


class FileListResponse(BaseModel):
    """文件列表响应"""
    files: List[FileInfo]
    total: int
    page: int
    page_size: int
    total_pages: int


class FileDownloadRequest(BaseModel):
    """文件下载请求"""
    file_id: str = Field(..., description="文件ID")
    download_type: str = Field(default="direct", description="下载类型: direct/url")


class FileDeleteRequest(BaseModel):
    """文件删除请求"""
    file_ids: List[str] = Field(..., description="文件ID列表")
    force: bool = Field(default=False, description="强制删除")


class BatchUploadRequest(BaseModel):
    """批量上传请求"""
    storage_type: StorageType = StorageType.LOCAL
    category: FileCategory = FileCategory.OTHER
    folder: Optional[str] = Field(default="", description="文件夹路径")
    overwrite: bool = Field(default=False, description="是否覆盖同名文件")


class FileOperationResponse(BaseModel):
    """文件操作响应"""
    success: bool = True
    message: str = "操作成功"
    file_info: Optional[FileInfo] = None
    files: Optional[List[FileInfo]] = None
    error_details: Optional[Dict[str, Any]] = None


class OSSConfig(BaseModel):
    """阿里云OSS配置"""
    access_key_id: str
    access_key_secret: str
    endpoint: str
    bucket_name: str
    region: Optional[str] = None
    custom_domain: Optional[str] = None


class LocalStorageConfig(BaseModel):
    """本地存储配置"""
    base_path: str = Field(default="./uploads", description="基础存储路径")
    base_url: str = Field(default="http://localhost:8001/files", description="访问基础URL")
    create_date_folder: bool = Field(default=True, description="是否创建日期文件夹")
    max_folder_files: int = Field(default=1000, description="单个文件夹最大文件数")


class FileServiceConfig(BaseModel):
    """文件服务配置"""
    default_storage: StorageType = StorageType.LOCAL
    local_config: LocalStorageConfig = LocalStorageConfig()
    oss_config: Optional[OSSConfig] = None
    upload_config: UploadConfig = UploadConfig()
    enable_thumbnail: bool = Field(default=True, description="是否启用缩略图")
    thumbnail_sizes: List[str] = Field(default=["150x150", "300x300"], description="缩略图尺寸")