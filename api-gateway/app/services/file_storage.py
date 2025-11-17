"""
文件存储服务
支持本地存储和阿里云OSS
"""
import os
import uuid
import hashlib
import mimetypes
from datetime import datetime
from typing import Optional, List, Tuple, BinaryIO
from pathlib import Path
import aiofiles
import oss2
try:
    from PIL import Image
except ImportError:
    Image = None
try:
    import magic
except ImportError:
    magic = None

from ..models import (
    FileInfo, StorageType, FileCategory, OSSConfig, 
    LocalStorageConfig, FileServiceConfig
)


class FileStorageService:
    """文件存储服务基类"""
    
    def __init__(self, config: FileServiceConfig):
        self.config = config
        
    async def upload_file(
        self, 
        file_content: bytes, 
        original_name: str,
        storage_type: StorageType,
        category: FileCategory = FileCategory.OTHER,
        folder: str = "",
        custom_name: Optional[str] = None,
        uploader: Optional[str] = None
    ) -> FileInfo:
        """上传文件"""
        raise NotImplementedError
        
    async def download_file(self, file_path: str) -> Tuple[bytes, str]:
        """下载文件"""
        raise NotImplementedError
        
    async def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        raise NotImplementedError
        
    async def get_file_url(self, file_path: str) -> str:
        """获取文件访问URL"""
        raise NotImplementedError
        
    def _generate_file_id(self) -> str:
        """生成文件ID"""
        return str(uuid.uuid4())
        
    def _get_file_extension(self, filename: str) -> str:
        """获取文件扩展名"""
        return Path(filename).suffix.lower()
        
    def _get_content_type(self, filename: str, file_content: bytes) -> str:
        """获取文件MIME类型"""
        # 首先尝试通过文件名获取
        content_type, _ = mimetypes.guess_type(filename)
        if content_type:
            return content_type
            
        # 通过文件内容检测
        if magic:
            try:
                mime = magic.from_buffer(file_content, mime=True)
                return mime
            except:
                pass
        return "application/octet-stream"
            
    def _categorize_file(self, content_type: str) -> FileCategory:
        """根据MIME类型分类文件"""
        if content_type.startswith('image/'):
            return FileCategory.IMAGE
        elif content_type.startswith('video/'):
            return FileCategory.VIDEO
        elif content_type.startswith('audio/'):
            return FileCategory.AUDIO
        elif content_type in ['application/pdf', 'application/msword', 
                             'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                             'text/plain']:
            return FileCategory.DOCUMENT
        else:
            return FileCategory.OTHER
            
    def _generate_file_path(
        self, 
        file_id: str, 
        original_name: str, 
        category: FileCategory,
        folder: str = "",
        custom_name: Optional[str] = None
    ) -> str:
        """生成文件存储路径"""
        # 获取文件扩展名
        ext = self._get_file_extension(original_name)
        
        # 确定文件名
        if custom_name:
            filename = f"{custom_name}{ext}"
        else:
            filename = f"{file_id}{ext}"
            
        # 构建路径
        path_parts = []
        
        # 添加分类目录
        path_parts.append(category.value)
        
        # 添加日期目录
        if self.config.local_config.create_date_folder:
            today = datetime.now()
            path_parts.extend([str(today.year), f"{today.month:02d}", f"{today.day:02d}"])
            
        # 添加自定义文件夹
        if folder:
            path_parts.append(folder.strip('/'))
            
        # 添加文件名
        path_parts.append(filename)
        
        return '/'.join(path_parts)


class LocalFileStorage(FileStorageService):
    """本地文件存储"""
    
    def __init__(self, config: FileServiceConfig):
        super().__init__(config)
        self.base_path = Path(config.local_config.base_path)
        self.base_url = config.local_config.base_url.rstrip('/')
        
        # 确保基础目录存在
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    async def upload_file(
        self, 
        file_content: bytes, 
        original_name: str,
        storage_type: StorageType,
        category: FileCategory = FileCategory.OTHER,
        folder: str = "",
        custom_name: Optional[str] = None,
        uploader: Optional[str] = None
    ) -> FileInfo:
        """上传文件到本地存储"""
        
        # 生成文件ID和路径
        file_id = self._generate_file_id()
        file_path = self._generate_file_path(file_id, original_name, category, folder, custom_name)
        
        # 完整的文件系统路径
        full_path = self.base_path / file_path
        
        # 确保目录存在
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        async with aiofiles.open(full_path, 'wb') as f:
            await f.write(file_content)
            
        # 获取文件信息
        content_type = self._get_content_type(original_name, file_content)
        file_size = len(file_content)
        
        # 生成缩略图（如果是图片）
        if category == FileCategory.IMAGE and self.config.enable_thumbnail:
            await self._generate_thumbnails(full_path, file_path)
            
        return FileInfo(
            file_id=file_id,
            original_name=original_name,
            file_name=full_path.name,
            file_path=file_path,
            file_url=f"{self.base_url}/{file_path}",
            file_size=file_size,
            content_type=content_type,
            category=category,
            storage_type=StorageType.LOCAL,
            upload_time=datetime.now(),
            uploader=uploader
        )
        
    async def download_file(self, file_path: str) -> Tuple[bytes, str]:
        """从本地存储下载文件"""
        full_path = self.base_path / file_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
            
        async with aiofiles.open(full_path, 'rb') as f:
            content = await f.read()
            
        content_type = self._get_content_type(full_path.name, content)
        return content, content_type
        
    async def delete_file(self, file_path: str) -> bool:
        """删除本地文件"""
        try:
            full_path = self.base_path / file_path
            
            if full_path.exists():
                full_path.unlink()
                
                # 删除缩略图
                await self._delete_thumbnails(file_path)
                
                return True
            return False
        except Exception:
            return False
            
    async def get_file_url(self, file_path: str) -> str:
        """获取本地文件访问URL"""
        return f"{self.base_url}/{file_path}"
        
    async def _generate_thumbnails(self, original_path: Path, file_path: str):
        """生成缩略图"""
        if not Image:
            return
            
        try:
            with Image.open(original_path) as img:
                for size_str in self.config.thumbnail_sizes:
                    width, height = map(int, size_str.split('x'))
                    
                    # 创建缩略图
                    thumbnail = img.copy()
                    thumbnail.thumbnail((width, height), Image.Resampling.LANCZOS)
                    
                    # 缩略图路径
                    thumb_path = self.base_path / f"thumbnails/{file_path}_{size_str}.jpg"
                    thumb_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 保存缩略图
                    thumbnail.save(thumb_path, "JPEG", quality=85)
                    
        except Exception as e:
            # 缩略图生成失败不影响主流程
            print(f"生成缩略图失败: {e}")
            
    async def _delete_thumbnails(self, file_path: str):
        """删除缩略图"""
        try:
            for size_str in self.config.thumbnail_sizes:
                thumb_path = self.base_path / f"thumbnails/{file_path}_{size_str}.jpg"
                if thumb_path.exists():
                    thumb_path.unlink()
        except Exception:
            pass


class OSSFileStorage(FileStorageService):
    """阿里云OSS文件存储"""
    
    def __init__(self, config: FileServiceConfig):
        super().__init__(config)
        
        if not config.oss_config:
            raise ValueError("OSS配置不能为空")
            
        self.oss_config = config.oss_config
        
        # 初始化OSS客户端
        auth = oss2.Auth(self.oss_config.access_key_id, self.oss_config.access_key_secret)
        self.bucket = oss2.Bucket(auth, self.oss_config.endpoint, self.oss_config.bucket_name)
        
    async def upload_file(
        self, 
        file_content: bytes, 
        original_name: str,
        storage_type: StorageType,
        category: FileCategory = FileCategory.OTHER,
        folder: str = "",
        custom_name: Optional[str] = None,
        uploader: Optional[str] = None
    ) -> FileInfo:
        """上传文件到阿里云OSS"""
        
        # 生成文件ID和路径
        file_id = self._generate_file_id()
        file_path = self._generate_file_path(file_id, original_name, category, folder, custom_name)
        
        # 获取文件信息
        content_type = self._get_content_type(original_name, file_content)
        file_size = len(file_content)
        
        # 上传到OSS
        result = self.bucket.put_object(
            file_path, 
            file_content,
            headers={'Content-Type': content_type}
        )
        
        # 生成访问URL
        if self.oss_config.custom_domain:
            file_url = f"https://{self.oss_config.custom_domain}/{file_path}"
        else:
            file_url = f"https://{self.oss_config.bucket_name}.{self.oss_config.endpoint}/{file_path}"
            
        return FileInfo(
            file_id=file_id,
            original_name=original_name,
            file_name=Path(file_path).name,
            file_path=file_path,
            file_url=file_url,
            file_size=file_size,
            content_type=content_type,
            category=category,
            storage_type=StorageType.OSS,
            upload_time=datetime.now(),
            uploader=uploader,
            metadata={"etag": result.etag}
        )
        
    async def download_file(self, file_path: str) -> Tuple[bytes, str]:
        """从阿里云OSS下载文件"""
        try:
            result = self.bucket.get_object(file_path)
            content = result.read()
            content_type = result.headers.get('Content-Type', 'application/octet-stream')
            return content, content_type
        except oss2.exceptions.NoSuchKey:
            raise FileNotFoundError(f"文件不存在: {file_path}")
            
    async def delete_file(self, file_path: str) -> bool:
        """删除OSS文件"""
        try:
            self.bucket.delete_object(file_path)
            return True
        except Exception:
            return False
            
    async def get_file_url(self, file_path: str) -> str:
        """获取OSS文件访问URL"""
        if self.oss_config.custom_domain:
            return f"https://{self.oss_config.custom_domain}/{file_path}"
        else:
            return f"https://{self.oss_config.bucket_name}.{self.oss_config.endpoint}/{file_path}"
            
    async def get_signed_url(self, file_path: str, expires: int = 3600) -> str:
        """获取OSS文件签名URL（用于私有访问）"""
        return self.bucket.sign_url('GET', file_path, expires)


class FileStorageManager:
    """文件存储管理器"""
    
    def __init__(self, config: FileServiceConfig):
        self.config = config
        self.local_storage = LocalFileStorage(config)
        self.oss_storage = OSSFileStorage(config) if config.oss_config else None
        
    def get_storage(self, storage_type: StorageType) -> FileStorageService:
        """获取存储服务实例"""
        if storage_type == StorageType.LOCAL:
            return self.local_storage
        elif storage_type == StorageType.OSS:
            if not self.oss_storage:
                raise ValueError("OSS存储未配置")
            return self.oss_storage
        else:
            raise ValueError(f"不支持的存储类型: {storage_type}")