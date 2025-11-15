"""
共享工具模块
定义系统中各服务共用的工具函数
"""
import uuid
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext


# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_id() -> str:
    """生成唯一ID"""
    return str(uuid.uuid4())


def generate_order_number() -> str:
    """生成订单号"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = str(uuid.uuid4())[:8].upper()
    return f"ORD{timestamp}{random_suffix}"


def generate_payment_id() -> str:
    """生成支付ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = str(uuid.uuid4())[:8].upper()
    return f"PAY{timestamp}{random_suffix}"


def generate_shipping_id() -> str:
    """生成发货ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = str(uuid.uuid4())[:8].upper()
    return f"SHP{timestamp}{random_suffix}"


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


def calculate_signature(data: Dict[str, Any], secret_key: str) -> str:
    """计算签名"""
    # 按键名排序
    sorted_items = sorted(data.items())
    # 拼接字符串
    sign_string = "&".join([f"{k}={v}" for k, v in sorted_items])
    # 添加密钥
    sign_string += f"&key={secret_key}"
    # 计算MD5
    return hashlib.md5(sign_string.encode()).hexdigest().upper()


def verify_signature(data: Dict[str, Any], signature: str, secret_key: str) -> bool:
    """验证签名"""
    calculated_signature = calculate_signature(data, secret_key)
    return hmac.compare_digest(calculated_signature, signature)


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


def format_response(success: bool = True, message: str = "操作成功", data: Any = None, error_code: str = None) -> Dict[str, Any]:
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