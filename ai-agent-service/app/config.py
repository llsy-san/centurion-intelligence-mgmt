"""
AI智能代理服务配置
"""
import os
from typing import Optional, List
from pydantic_settings import BaseSettings


class ServiceConfig(BaseSettings):
    """AI智能代理服务配置"""
    # 应用基础配置
    app_name: str = "百夫长智能管理系统 - AI智能代理服务"
    version: str = "1.0.0"
    debug: bool = True
    
    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8005
    
    # 数据库配置
    database_url: str = "postgresql://postgres:centurion123@postgres:5432/centurion_db"
    
    # Redis配置
    redis_url: str = "redis://:centurion123@redis:6379"
    
    # AI模型配置
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    default_model: str = "gpt-3.5-turbo"
    
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"


# 全局配置实例
config = ServiceConfig()