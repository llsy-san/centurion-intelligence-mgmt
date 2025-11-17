# -*- coding: utf-8 -*-
import logging
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from passlib.context import CryptContext

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def setup_logging(log_level: str = "INFO", log_format: str = None):
    """设置日志配置"""
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(),
        ]
    )
    
    # 设置第三方库日志级别
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    # 返回 logger 实例
    return logging.getLogger("api-gateway")


def format_response(
    success: bool = True,
    data: Any = None,
    message: str = "",
    code: int = 200
) -> Dict[str, Any]:
    """格式化API响应"""
    return {
        "success": success,
        "code": code,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }


def create_error_response(
    message: str,
    code: int = 400,
    details: Any = None
) -> JSONResponse:
    """创建错误响应"""
    response_data = format_response(
        success=False,
        message=message,
        code=code,
        data=details
    )
    return JSONResponse(
        status_code=code,
        content=response_data
    )


def validate_file_type(content_type: str, allowed_types: list) -> bool:
    """验证文件类型"""
    return content_type in allowed_types


def validate_file_size(file_size: int, max_size: int) -> bool:
    """验证文件大小"""
    return file_size <= max_size


class ServiceException(HTTPException):
    """自定义服务异常"""
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=message)


class DatabaseException(ServiceException):
    """数据库异常"""
    def __init__(self, message: str = "数据库操作失败"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


class AuthenticationException(ServiceException):
    """认证异常"""
    def __init__(self, message: str = "认证失败"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class AuthorizationException(ServiceException):
    """授权异常"""
    def __init__(self, message: str = "权限不足"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class ValidationException(ServiceException):
    """验证异常"""
    def __init__(self, message: str = "数据验证失败"):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)


def hash_password(password: str) -> str:
    """密码哈希"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], secret_key: str, expires_delta: Optional[timedelta] = None) -> str:
    """创建JWT访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm="HS256")
    return encoded_jwt


def verify_token(token: str, secret_key: str) -> Optional[Dict[str, Any]]:
    """验证JWT令牌"""
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except JWTError:
        return None