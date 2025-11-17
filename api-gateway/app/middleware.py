"""
API网关中间件
定义限流、日志等中间件
"""
import time
import logging
from collections import defaultdict, deque
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Deque

logger = logging.getLogger("api-gateway-middleware")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, Deque[float]] = defaultdict(deque)
    
    async def dispatch(self, request: Request, call_next):
        # 获取客户端IP
        client_ip = request.client.host
        
        # 获取当前时间
        current_time = time.time()
        
        # 清理过期的请求记录
        self._cleanup_expired_requests(client_ip, current_time)
        
        # 检查是否超过限制
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            logger.warning(f"限流触发: IP {client_ip} 超过每分钟 {self.requests_per_minute} 次请求限制")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="请求过于频繁，请稍后再试"
            )
        
        # 记录当前请求
        self.requests[client_ip].append(current_time)
        
        # 继续处理请求
        response = await call_next(request)
        
        return response
    
    def _cleanup_expired_requests(self, client_ip: str, current_time: float):
        """清理过期的请求记录"""
        minute_ago = current_time - 60
        
        while self.requests[client_ip] and self.requests[client_ip][0] < minute_ago:
            self.requests[client_ip].popleft()


class LoggingMiddleware(BaseHTTPMiddleware):
    """日志中间件"""
    
    async def dispatch(self, request: Request, call_next):
        # 记录请求开始时间
        start_time = time.time()
        
        # 记录请求信息
        logger.info(
            f"请求开始: {request.method} {request.url} "
            f"客户端: {request.client.host} "
            f"用户代理: {request.headers.get('user-agent', 'Unknown')}"
        )
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应信息
            logger.info(
                f"请求完成: {request.method} {request.url} "
                f"状态码: {response.status_code} "
                f"处理时间: {process_time:.3f}s"
            )
            
            return response
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录错误信息
            logger.error(
                f"请求失败: {request.method} {request.url} "
                f"错误: {str(e)} "
                f"处理时间: {process_time:.3f}s"
            )
            
            raise