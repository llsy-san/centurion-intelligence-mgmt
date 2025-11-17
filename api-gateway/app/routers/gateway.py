"""
API网关路由
定义网关特有的API接口
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import timedelta
import sys
import os

# 添加共享模块到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../shared'))

from ..models import BaseResponse
from ..config import GatewayConfig
from ..utils import format_response, create_access_token, verify_token, hash_password, verify_password

router = APIRouter()
security = HTTPBearer()
config = GatewayConfig()


@router.post("/auth/login", response_model=BaseResponse)
async def login(username: str, password: str):
    """用户登录"""
    try:
        # 这里应该从数据库验证用户信息
        # 暂时使用硬编码的用户信息进行演示
        if username == "admin" and password == "password":
            # 创建访问令牌
            access_token_expires = timedelta(minutes=config.jwt_expire_minutes)
            access_token = create_access_token(
                data={"sub": username, "user_id": "admin_001"},
                secret_key=config.jwt_secret_key,
                expires_delta=access_token_expires
            )
            
            return format_response(
                message="登录成功",
                data={
                    "access_token": access_token,
                    "token_type": "bearer",
                    "expires_in": config.jwt_expire_minutes * 60
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败"
        )


@router.post("/auth/refresh", response_model=BaseResponse)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """刷新访问令牌"""
    try:
        token = credentials.credentials
        payload = verify_token(token, config.jwt_secret_key)
        
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的访问令牌"
            )
        
        # 创建新的访问令牌
        access_token_expires = timedelta(minutes=config.jwt_expire_minutes)
        new_access_token = create_access_token(
            data={"sub": payload["sub"], "user_id": payload.get("user_id")},
            secret_key=config.jwt_secret_key,
            expires_delta=access_token_expires
        )
        
        return format_response(
            message="令牌刷新成功",
            data={
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": config.jwt_expire_minutes * 60
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="令牌刷新失败"
        )


@router.get("/system/info", response_model=BaseResponse)
async def get_system_info():
    """获取系统信息"""
    return format_response(
        message="获取系统信息成功",
        data={
            "system_name": "百夫长智能管理系统",
            "version": "1.0.0",
            "services": {
                "order_service": config.order_service_url,
                "payment_service": config.payment_service_url,
                "shipping_service": config.shipping_service_url
            }
        }
    )