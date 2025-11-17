# -*- coding: utf-8 -*-
"""
任务调度服务配置
"""
import os
from pydantic_settings import BaseSettings


class TaskSchedulerConfig(BaseSettings):
    """任务调度服务配置"""
    # 应用基础配置
    app_name: str = "百夫长智能管理系统 - 任务调度服务"
    version: str = "1.0.0"
    debug: bool = False
    
    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8006
    
    # 数据库配置
    database_url: str = "postgresql+asyncpg://postgres:centurion123@postgres:5432/centurion_db"
    
    # Redis配置
    redis_url: str = "redis://:centurion123@redis:6379/0"
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: str = "centurion123"
    redis_db: int = 0
    
    # 服务地址配置
    order_service_url: str = "http://order-service:8002"
    payment_service_url: str = "http://payment-service:8003"
    shipping_service_url: str = "http://shipping-service:8004"
    ai_agent_service_url: str = "http://ai-agent-service:8005"
    
    # 第三方API配置
    third_party_api_url: str = "https://api.third-party.com"
    third_party_api_key: str = "your-api-key"
    
    # Celery 配置
    CELERY_BROKER_URL: str = "redis://:centurion123@redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://:centurion123@redis:6379/0"
    
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"


# 全局配置实例
config = TaskSchedulerConfig()

# 兼容性别名和函数
Settings = TaskSchedulerConfig

def get_settings():
    """获取配置实例"""
    return config