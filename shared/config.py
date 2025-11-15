"""
共享配置模块
定义所有服务的配置类
"""
import os
from typing import Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseModel):
    """数据库配置"""
    host: str = "localhost"
    port: int = 5432
    username: str = "postgres"
    password: str = "password"
    database: str = "centurion_intelligence_db"
    
    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class RedisConfig(BaseModel):
    """Redis配置"""
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    
    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class BaseServiceConfig(BaseSettings):
    """基础服务配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # 数据库配置
    database: DatabaseConfig = DatabaseConfig()
    
    # Redis配置
    redis: RedisConfig = RedisConfig()
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"


class GatewayConfig(BaseServiceConfig):
    """API网关配置"""
    port: int = 8000
    jwt_secret_key: str = "your-secret-key-here"
    jwt_expire_minutes: int = 1440  # 24小时
    
    # 服务地址配置
    order_service_url: str = "http://localhost:8001"
    payment_service_url: str = "http://localhost:8002"
    shipping_service_url: str = "http://localhost:8003"
    task_scheduler_service_url: str = "http://localhost:8004"


class OrderServiceConfig(BaseServiceConfig):
    """订单服务配置"""
    port: int = 8001


class PaymentServiceConfig(BaseServiceConfig):
    """支付服务配置"""
    port: int = 8002
    
    # 支付相关配置
    wechat_app_id: str = ""
    wechat_mch_id: str = ""
    wechat_api_key: str = ""
    
    alipay_app_id: str = ""
    alipay_private_key: str = ""
    alipay_public_key: str = ""


class ShippingServiceConfig(BaseServiceConfig):
    """物流服务配置"""
    port: int = 8003


class TaskSchedulerConfig(BaseServiceConfig):
    """定时任务服务配置"""
    port: int = 8004
    
    # 第三方API配置
    third_party_api_url: str = "https://api.third-party.com"
    third_party_api_key: str = "your-api-key"
    
    # 微信支付API配置
    wechat_pay_api_url: str = "https://api.mch.weixin.qq.com"
    wechat_pay_app_id: str = ""
    wechat_pay_mch_id: str = ""
    wechat_pay_api_key: str = ""


class AIAgentConfig(BaseServiceConfig):
    """AI智能体服务配置"""
    port: int = 8005
    
    # AI模型配置
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    default_model: str = "gpt-3.5-turbo"