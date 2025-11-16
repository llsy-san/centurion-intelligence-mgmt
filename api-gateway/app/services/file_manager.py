"""
文件管理服务
提供文件的CRUD操作和业务逻辑
"""
import os
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import aiofiles

from ..file_models import (
    FileInfo, FileListRequest, FileListResponse, StorageType, 
    FileCategory, FileServiceConfig, FileUploadRequest,
    FileDeleteRequest, BatchUploadRequest
)
from .file_storage import FileStorageManager


class FileManager:
    """文件管理器"""
    
    def __init__(self, config: FileServiceConfig):
        self.config = config
        self.storage_manager = FileStorageManager(config)
        self.metadata_file = Path("file_metadata.json")
        self._file_registry: Dict[str, FileInfo] = {}
        
    async def initialize(self):
        """初始化文件管理器"""
        await self._load_file_registry()
        
    async def upload_file(
        self,
        file_content: bytes,
        original_name: str,
        request: FileUploadRequest,
        uploader: Optional[str] = None
    ) -> FileInfo:
        """上传单个文件"""
        
        # 验证文件
        await self._validate_file(file_content, original_name)
        
        # 获取存储服务
        storage = self.storage_manager.get_storage(request.storage_type)
        
        # 上传文件
        file_info = await storage.upload_file(
            file_content=file_content,
            original_name=original_name,
            storage_type=request.storage_type,
            category=request.category,
            folder=request.folder or "",
            custom_name=request.custom_name,
            uploader=uploader
        )
        
        # 注册文件信息
        await self._register_file(file_info)
        
        return file_info
        
    async def upload_multiple_files(
        self,
        files_data: List[tuple],  # [(file_content, original_name), ...]
        request: BatchUploadRequest,
        uploader: Optional[str] = None
    ) -> List[FileInfo]:
        """批量上传文件"""
        
        uploaded_files = []
        failed_files = []
        
        for file_content, original_name in files_data:
            try:
                # 创建单个文件上传请求
                single_request = FileUploadRequest(
                    storage_type=request.storage_type,
                    category=request.category,
                    folder=request.folder,
                    overwrite=request.overwrite
                )
                
                file_info = await self.upload_file(
                    file_content, original_name, single_request, uploader
                )
                uploaded_files.append(file_info)
                
            except Exception as e:
                failed_files.append({
                    "filename": original_name,
                    "error": str(e)
                })
                
        return uploaded_files
        
    async def download_file(self, file_id: str) -> tuple[bytes, str, FileInfo]:
        """下载文件"""
        
        # 获取文件信息
        file_info = await self._get_file_info(file_id)
        if not file_info:
            raise FileNotFoundError(f"文件不存在: {file_id}")
            
        # 获取存储服务
        storage = self.storage_manager.get_storage(file_info.storage_type)
        
        # 下载文件
        content, content_type = await storage.download_file(file_info.file_path)
        
        return content, content_type, file_info
        
    async def get_file_url(self, file_id: str, signed: bool = False) -> str:
        """获取文件访问URL"""
        
        file_info = await self._get_file_info(file_id)
        if not file_info:
            raise FileNotFoundError(f"文件不存在: {file_id}")
            
        storage = self.storage_manager.get_storage(file_info.storage_type)
        
        if signed and file_info.storage_type == StorageType.OSS:
            # 获取签名URL（用于私有文件）
            return await storage.get_signed_url(file_info.file_path)
        else:
            return await storage.get_file_url(file_info.file_path)
            
    async def delete_files(self, request: FileDeleteRequest) -> Dict[str, Any]:
        """删除文件"""
        
        deleted_files = []
        failed_files = []
        
        for file_id in request.file_ids:
            try:
                file_info = await self._get_file_info(file_id)
                if not file_info:
                    failed_files.append({
                        "file_id": file_id,
                        "error": "文件不存在"
                    })
                    continue
                    
                # 获取存储服务
                storage = self.storage_manager.get_storage(file_info.storage_type)
                
                # 删除文件
                success = await storage.delete_file(file_info.file_path)
                
                if success:
                    # 从注册表中移除
                    await self._unregister_file(file_id)
                    deleted_files.append(file_info)
                else:
                    failed_files.append({
                        "file_id": file_id,
                        "error": "删除失败"
                    })
                    
            except Exception as e:
                failed_files.append({
                    "file_id": file_id,
                    "error": str(e)
                })
                
        return {
            "deleted_count": len(deleted_files),
            "failed_count": len(failed_files),
            "deleted_files": deleted_files,
            "failed_files": failed_files
        }
        
    async def list_files(self, request: FileListRequest) -> FileListResponse:
        """获取文件列表"""
        
        # 过滤文件
        filtered_files = []
        
        for file_info in self._file_registry.values():
            # 按分类过滤
            if request.category and file_info.category != request.category:
                continue
                
            # 按存储类型过滤
            if request.storage_type and file_info.storage_type != request.storage_type:
                continue
                
            # 按文件夹过滤
            if request.folder and not file_info.file_path.startswith(request.folder):
                continue
                
            # 按关键词搜索
            if request.keyword:
                keyword = request.keyword.lower()
                if (keyword not in file_info.original_name.lower() and 
                    keyword not in file_info.file_name.lower()):
                    continue
                    
            filtered_files.append(file_info)
            
        # 排序（按上传时间倒序）
        filtered_files.sort(key=lambda x: x.upload_time, reverse=True)
        
        # 分页
        total = len(filtered_files)
        start_idx = (request.page - 1) * request.page_size
        end_idx = start_idx + request.page_size
        page_files = filtered_files[start_idx:end_idx]
        
        total_pages = (total + request.page_size - 1) // request.page_size
        
        return FileListResponse(
            files=page_files,
            total=total,
            page=request.page,
            page_size=request.page_size,
            total_pages=total_pages
        )
        
    async def get_file_info(self, file_id: str) -> Optional[FileInfo]:
        """获取文件信息"""
        return await self._get_file_info(file_id)
        
    async def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        
        stats = {
            "total_files": len(self._file_registry),
            "storage_breakdown": {},
            "category_breakdown": {},
            "total_size": 0
        }
        
        for file_info in self._file_registry.values():
            # 存储类型统计
            storage_type = file_info.storage_type.value
            if storage_type not in stats["storage_breakdown"]:
                stats["storage_breakdown"][storage_type] = {"count": 0, "size": 0}
            stats["storage_breakdown"][storage_type]["count"] += 1
            stats["storage_breakdown"][storage_type]["size"] += file_info.file_size
            
            # 分类统计
            category = file_info.category.value
            if category not in stats["category_breakdown"]:
                stats["category_breakdown"][category] = {"count": 0, "size": 0}
            stats["category_breakdown"][category]["count"] += 1
            stats["category_breakdown"][category]["size"] += file_info.file_size
            
            # 总大小
            stats["total_size"] += file_info.file_size
            
        return stats
        
    async def _validate_file(self, file_content: bytes, filename: str):
        """验证文件"""
        
        # 检查文件大小
        if len(file_content) > self.config.upload_config.max_file_size:
            raise ValueError(f"文件大小超过限制: {len(file_content)} > {self.config.upload_config.max_file_size}")
            
        # 检查文件扩展名
        file_ext = Path(filename).suffix.lower()
        if (self.config.upload_config.allowed_extensions and 
            file_ext not in self.config.upload_config.allowed_extensions):
            raise ValueError(f"不支持的文件类型: {file_ext}")
            
        # 检查文件内容（防止恶意文件）
        if len(file_content) == 0:
            raise ValueError("文件内容为空")
            
    async def _register_file(self, file_info: FileInfo):
        """注册文件信息"""
        self._file_registry[file_info.file_id] = file_info
        await self._save_file_registry()
        
    async def _unregister_file(self, file_id: str):
        """注销文件信息"""
        if file_id in self._file_registry:
            del self._file_registry[file_id]
            await self._save_file_registry()
            
    async def _get_file_info(self, file_id: str) -> Optional[FileInfo]:
        """获取文件信息"""
        return self._file_registry.get(file_id)
        
    async def _load_file_registry(self):
        """加载文件注册表"""
        try:
            if self.metadata_file.exists():
                async with aiofiles.open(self.metadata_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    data = json.loads(content)
                    
                    for file_id, file_data in data.items():
                        # 转换时间字符串为datetime对象
                        if isinstance(file_data.get('upload_time'), str):
                            file_data['upload_time'] = datetime.fromisoformat(file_data['upload_time'])
                            
                        self._file_registry[file_id] = FileInfo(**file_data)
                        
        except Exception as e:
            print(f"加载文件注册表失败: {e}")
            self._file_registry = {}
            
    async def _save_file_registry(self):
        """保存文件注册表"""
        try:
            data = {}
            for file_id, file_info in self._file_registry.items():
                file_data = file_info.dict()
                # 转换datetime对象为字符串
                if isinstance(file_data.get('upload_time'), datetime):
                    file_data['upload_time'] = file_data['upload_time'].isoformat()
                data[file_id] = file_data
                
            async with aiofiles.open(self.metadata_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=2))
                
        except Exception as e:
            print(f"保存文件注册表失败: {e}")
            
    async def cleanup_orphaned_files(self):
        """清理孤立文件（注册表中存在但实际文件不存在）"""
        
        orphaned_files = []
        
        for file_id, file_info in list(self._file_registry.items()):
            try:
                storage = self.storage_manager.get_storage(file_info.storage_type)
                
                # 尝试获取文件信息来检查文件是否存在
                try:
                    await storage.download_file(file_info.file_path)
                except FileNotFoundError:
                    # 文件不存在，标记为孤立文件
                    orphaned_files.append(file_id)
                    await self._unregister_file(file_id)
                    
            except Exception as e:
                print(f"检查文件 {file_id} 时出错: {e}")
                
        return orphaned_files