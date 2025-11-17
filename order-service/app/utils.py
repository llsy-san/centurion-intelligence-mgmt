"""
订单服务工具模块
"""
import uuid
import logging
from datetime import datetime
from typing import Any, Dict, Optional


def generate_id() -> str:
    """生成唯一ID"""
    return str(uuid.uuid4())


def generate_order_number() -> str:
    """生成订单号"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = str(uuid.uuid4())[:8].upper()
    return f"ORD{timestamp}{random_suffix}"


def setup_logging(service_name: str, level: str = "INFO") -> logging.Logger:
    """设置日志"""
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))
    
    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    # 添加处理器到日志器
    logger.addHandler(console_handler)
    
    return logger


def format_response(success: bool = True, message: str = "操作成功", data: Any = None, error_code: Optional[str] = None) -> Dict[str, Any]:
    """格式化响应"""
    response = {
        "success": success,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    if error_code:
        response["error_code"] = error_code
    
    return response


def serialize_datetime(obj: Any) -> Any:
    """序列化日期时间对象"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")