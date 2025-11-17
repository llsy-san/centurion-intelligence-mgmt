"""
订单服务配置
"""
from pydantic_settings import BaseSettings


class OrderServiceConfig(BaseSettings):
    """订单服务配置"""
    # 应用基础配置
    app_name: str = "百夫长智能管理系统 - 订单服务"
    version: str = "1.0.0"
    debug: bool = True
    
    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8002
    
    # 数据库配置
    database_url: str = "postgresql://postgres:centurion123@postgres:5432/centurion_db"
    
    # Redis配置
    redis_url: str = "redis://:centurion123@redis:6379"
    
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"


# 全局配置实例
config = OrderServiceConfig()