"""
支付服务配置
"""
from pydantic_settings import BaseSettings


class PaymentServiceConfig(BaseSettings):
    """支付服务配置"""
    # 应用基础配置
    app_name: str = "百夫长智能管理系统 - 支付服务"
    version: str = "1.0.0"
    debug: bool = True
    
    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8003
    
    # 数据库配置
    database_url: str = "postgresql://postgres:centurion123@postgres:5432/centurion_db"
    
    # Redis配置
    redis_url: str = "redis://:centurion123@redis:6379"
    
    # 支付相关配置
    wechat_app_id: str = ""
    wechat_mch_id: str = ""
    wechat_api_key: str = ""
    
    alipay_app_id: str = ""
    alipay_private_key: str = ""
    alipay_public_key: str = ""
    
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"


# 全局配置实例
config = PaymentServiceConfig()