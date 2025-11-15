"""
任务调度服务数据模型
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel


class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None