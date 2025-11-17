# -*- coding: utf-8 -*-
"""
任务调度服务数据模型
"""
try:
    from typing import Optional, Dict, Any
except ImportError:
    # Python 2.7 fallback
    Optional = None
    Dict = dict
    Any = object

from pydantic import BaseModel


class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Any] = None
    error_code: Optional[str] = None