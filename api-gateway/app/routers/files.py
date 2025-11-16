"""
文件管理API路由
"""
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse, JSONResponse
import io

from ..file_models import (
    FileUploadRequest, FileListRequest, FileListResponse,
    FileDeleteRequest, BatchUploadRequest, FileOperationResponse,
    StorageType, FileCategory, FileInfo
)
from ..services.file_manager import FileManager
from ..config.file_config import file_service_config

router = APIRouter(prefix="/files", tags=["文件管理"])

# 全局文件管理器实例
file_manager = FileManager(file_service_config)


@router.on_event("startup")
async def startup_event():
    """启动时初始化文件管理器"""
    await file_manager.initialize()


@router.post("/upload", response_model=FileOperationResponse, summary="上传单个文件")
async def upload_file(
    file: UploadFile = File(..., description="要上传的文件"),
    storage_type: StorageType = Form(default=StorageType.LOCAL, description="存储类型"),
    category: FileCategory = Form(default=FileCategory.OTHER, description="文件分类"),
    folder: Optional[str] = Form(default="", description="文件夹路径"),
    custom_name: Optional[str] = Form(default=None, description="自定义文件名"),
    overwrite: bool = Form(default=False, description="是否覆盖同名文件"),
    uploader: Optional[str] = Form(default=None, description="上传者")
):
    """上传单个文件"""
    try:
        # 读取文件内容
        file_content = await file.read()
        
        # 创建上传请求
        request = FileUploadRequest(
            storage_type=storage_type,
            category=category,
            folder=folder or "",
            custom_name=custom_name,
            overwrite=overwrite
        )
        
        # 上传文件
        file_info = await file_manager.upload_file(
            file_content=file_content,
            original_name=file.filename,
            request=request,
            uploader=uploader
        )
        
        return FileOperationResponse(
            success=True,
            message="文件上传成功",
            file_info=file_info
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件上传失败: {str(e)}")


@router.post("/upload/batch", response_model=FileOperationResponse, summary="批量上传文件")
async def upload_multiple_files(
    files: List[UploadFile] = File(..., description="要上传的文件列表"),
    storage_type: StorageType = Form(default=StorageType.LOCAL, description="存储类型"),
    category: FileCategory = Form(default=FileCategory.OTHER, description="文件分类"),
    folder: Optional[str] = Form(default="", description="文件夹路径"),
    overwrite: bool = Form(default=False, description="是否覆盖同名文件"),
    uploader: Optional[str] = Form(default=None, description="上传者")
):
    """批量上传文件"""
    try:
        # 准备文件数据
        files_data = []
        for file in files:
            content = await file.read()
            files_data.append((content, file.filename))
        
        # 创建批量上传请求
        request = BatchUploadRequest(
            storage_type=storage_type,
            category=category,
            folder=folder or "",
            overwrite=overwrite
        )
        
        # 批量上传
        uploaded_files = await file_manager.upload_multiple_files(
            files_data=files_data,
            request=request,
            uploader=uploader
        )
        
        return FileOperationResponse(
            success=True,
            message=f"成功上传 {len(uploaded_files)} 个文件",
            files=uploaded_files
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"批量上传失败: {str(e)}")


@router.get("/download/{file_id}", summary="下载文件")
async def download_file(file_id: str):
    """下载文件"""
    try:
        content, content_type, file_info = await file_manager.download_file(file_id)
        
        # 创建流式响应
        return StreamingResponse(
            io.BytesIO(content),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{file_info.original_name}",
                "Content-Length": str(len(content))
            }
        )
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="文件不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")


@router.get("/url/{file_id}", summary="获取文件访问URL")
async def get_file_url(
    file_id: str,
    signed: bool = Query(default=False, description="是否获取签名URL（用于私有文件）")
):
    """获取文件访问URL"""
    try:
        url = await file_manager.get_file_url(file_id, signed=signed)
        return {"file_url": url}
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="文件不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取URL失败: {str(e)}")


@router.post("/delete", response_model=FileOperationResponse, summary="删除文件")
async def delete_files(request: FileDeleteRequest):
    """删除文件"""
    try:
        result = await file_manager.delete_files(request)
        
        return FileOperationResponse(
            success=result["failed_count"] == 0,
            message=f"删除了 {result['deleted_count']} 个文件，失败 {result['failed_count']} 个",
            error_details=result if result["failed_count"] > 0 else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.post("/list", response_model=FileListResponse, summary="获取文件列表")
async def list_files(request: FileListRequest):
    """获取文件列表"""
    try:
        return await file_manager.list_files(request)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")


@router.get("/info/{file_id}", response_model=FileInfo, summary="获取文件信息")
async def get_file_info(file_id: str):
    """获取文件信息"""
    try:
        file_info = await file_manager.get_file_info(file_id)
        if not file_info:
            raise HTTPException(status_code=404, detail="文件不存在")
        return file_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件信息失败: {str(e)}")


@router.get("/stats", summary="获取存储统计信息")
async def get_storage_stats():
    """获取存储统计信息"""
    try:
        return await file_manager.get_storage_stats()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.post("/cleanup", summary="清理孤立文件")
async def cleanup_orphaned_files():
    """清理孤立文件（管理员功能）"""
    try:
        orphaned_files = await file_manager.cleanup_orphaned_files()
        
        return {
            "success": True,
            "message": f"清理了 {len(orphaned_files)} 个孤立文件",
            "orphaned_files": orphaned_files
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")


# 静态文件服务（用于本地存储的文件访问）
@router.get("/static/{file_path:path}", summary="访问本地存储文件")
async def serve_static_file(file_path: str):
    """提供本地存储文件的静态访问"""
    try:
        # 通过文件路径查找文件ID
        for file_id, file_info in file_manager._file_registry.items():
            if file_info.file_path == file_path and file_info.storage_type == StorageType.LOCAL:
                content, content_type, _ = await file_manager.download_file(file_id)
                
                return StreamingResponse(
                    io.BytesIO(content),
                    media_type=content_type,
                    headers={"Cache-Control": "public, max-age=3600"}
                )
                
        raise HTTPException(status_code=404, detail="文件不存在")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"访问文件失败: {str(e)}")