# API网关服务文档

## 📋 服务概述

API网关是百夫长智能管理系统的统一入口，负责请求路由、负载均衡、认证授权、限流熔断等功能。

## 🏗️ 服务架构

```
客户端请求 → API网关 → 后端微服务
    ↓           ↓           ↓
  认证授权   →  路由转发  →  业务处理
  限流控制   →  负载均衡  →  响应返回
  日志记录   →  错误处理  →  统一格式
```

## 🔧 技术栈

- **框架**: FastAPI 0.104+
- **认证**: JWT Token
- **限流**: Redis + 滑动窗口
- **路由**: 动态路由配置
- **监控**: 结构化日志 + 性能指标

## 📊 服务信息

| 属性 | 值 |
|------|-----|
| **服务名称** | api-gateway |
| **端口** | 8001 |
| **协议** | HTTP/HTTPS |
| **健康检查** | `/health` |
| **API文档** | `/docs` |
| **OpenAPI** | `/openapi.json` |

## 🚀 快速启动

### 使用Docker

```bash
# 启动API网关服务
make start-api

# 或直接使用脚本
./scripts/start-api-gateway.sh
```

### 本地开发

```bash
# 进入服务目录
cd api-gateway

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload --port 8001
```

## 📡 API接口

### 健康检查

```http
GET /health
```

**响应示例:**
```json
{
  "status": "healthy",
  "timestamp": "2024-11-16T10:00:00Z",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "redis": "connected"
  }
}
```

### 认证接口

#### 用户登录
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password"
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

#### 刷新Token
```http
POST /api/v1/auth/refresh
Authorization: Bearer <access_token>
```

#### 用户注销
```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
```

### 文件服务接口

#### 文件上传
```http
POST /api/v1/files/upload
Content-Type: multipart/form-data
Authorization: Bearer <access_token>

file: <binary_data>
storage_type: local|oss
category: image|document|video
```

**响应示例:**
```json
{
  "code": 200,
  "message": "文件上传成功",
  "data": {
    "file_id": "f123456789",
    "filename": "example.jpg",
    "size": 1024000,
    "url": "http://localhost:8001/api/v1/files/download/f123456789"
  }
}
```

#### 文件下载
```http
GET /api/v1/files/download/{file_id}
```

#### 获取文件信息
```http
GET /api/v1/files/info/{file_id}
Authorization: Bearer <access_token>
```

### 代理接口

API网关会将以下路径的请求代理到对应的微服务：

| 路径前缀 | 目标服务 | 端口 |
|----------|----------|------|
| `/api/v1/orders/` | 订单服务 | 8002 |
| `/api/v1/payments/` | 支付服务 | 8003 |
| `/api/v1/shipping/` | 物流服务 | 8004 |
| `/api/v1/ai/` | AI智能体 | 8005 |
| `/api/v1/tasks/` | 任务调度 | 8006 |

## 🔐 认证授权

### JWT Token认证

API网关使用JWT Token进行用户认证：

```python
# Token格式
{
  "sub": "user_id",
  "username": "admin",
  "exp": 1700000000,
  "iat": 1699999000,
  "roles": ["admin", "user"]
}
```

### 权限控制

支持基于角色的访问控制(RBAC)：

- **admin**: 管理员权限，可访问所有接口
- **user**: 普通用户权限，可访问基础功能
- **guest**: 访客权限，仅可访问公开接口

### 受保护的路由

需要认证的接口路径：
- `/api/v1/orders/*`
- `/api/v1/payments/*`
- `/api/v1/shipping/*`
- `/api/v1/ai/*`
- `/api/v1/tasks/*`
- `/api/v1/files/*` (除下载外)

## 🚦 限流控制

### 限流策略

| 用户类型 | 每分钟请求数 | 突发请求数 |
|----------|--------------|------------|
| **匿名用户** | 60 | 10 |
| **普通用户** | 120 | 20 |
| **VIP用户** | 300 | 50 |
| **管理员** | 600 | 100 |

### 限流响应

当触发限流时，返回429状态码：

```json
{
  "code": 429,
  "message": "请求过于频繁，请稍后再试",
  "data": {
    "retry_after": 60,
    "limit": 120,
    "remaining": 0
  }
}
```

## 🔄 负载均衡

### 负载均衡策略

- **轮询**: 默认策略，依次分发请求
- **权重轮询**: 根据服务权重分发
- **最少连接**: 选择连接数最少的服务
- **健康检查**: 自动剔除不健康的服务实例

### 服务发现

支持多种服务发现方式：
- **静态配置**: 在配置文件中指定服务地址
- **环境变量**: 通过环境变量动态配置
- **健康检查**: 定期检查服务健康状态

## 📊 监控指标

### 性能指标

- **请求总数**: 总请求计数
- **响应时间**: P50、P95、P99响应时间
- **错误率**: 4xx、5xx错误比例
- **QPS**: 每秒查询数
- **并发数**: 当前并发连接数

### 业务指标

- **认证成功率**: 登录成功比例
- **API调用分布**: 各接口调用频次
- **用户活跃度**: 活跃用户统计
- **文件上传量**: 文件上传统计

## 🛠️ 配置说明

### 环境变量

```bash
# 服务配置
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=8001
GATEWAY_DEBUG=true

# 认证配置
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# 限流配置
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# 后端服务配置
ORDER_SERVICE_URL=http://localhost:8002
PAYMENT_SERVICE_URL=http://localhost:8003
SHIPPING_SERVICE_URL=http://localhost:8004
AI_AGENT_SERVICE_URL=http://localhost:8005
TASK_SCHEDULER_SERVICE_URL=http://localhost:8006

# 数据库配置
DATABASE_URL=postgresql://postgres:password@localhost:5432/centurion_db
REDIS_URL=redis://localhost:6379/0
```

### 中间件配置

```python
# CORS配置
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["*"]
CORS_ALLOW_HEADERS=["*"]

# 安全头配置
SECURITY_HEADERS={
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block"
}
```

## 🐛 故障排除

### 常见问题

#### 1. 服务启动失败
```bash
# 检查端口占用
lsof -i :8001

# 查看服务日志
docker logs centurion-api-gateway

# 检查配置文件
cat .env | grep GATEWAY
```

#### 2. 认证失败
```bash
# 检查JWT配置
echo $JWT_SECRET_KEY

# 验证Token格式
curl -H "Authorization: Bearer <token>" http://localhost:8001/api/v1/auth/verify
```

#### 3. 代理失败
```bash
# 检查后端服务状态
curl http://localhost:8002/health
curl http://localhost:8003/health

# 查看代理日志
docker logs centurion-api-gateway | grep proxy
```

#### 4. 限流问题
```bash
# 检查Redis连接
docker exec centurion-redis redis-cli ping

# 查看限流配置
curl http://localhost:8001/api/v1/rate-limit/status
```

### 日志分析

```bash
# 查看访问日志
docker logs centurion-api-gateway | grep "GET\|POST\|PUT\|DELETE"

# 查看错误日志
docker logs centurion-api-gateway | grep ERROR

# 查看性能日志
docker logs centurion-api-gateway | grep "response_time"
```

## 🔧 开发指南

### 添加新的代理路由

```python
# 在 app/routers/gateway.py 中添加
@router.api_route(
    "/api/v1/new-service/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"]
)
async def proxy_new_service(request: Request, path: str):
    return await proxy_request(
        request, 
        f"http://new-service:8007/{path}"
    )
```

### 添加新的中间件

```python
# 在 app/middleware/ 中创建新中间件
class CustomMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        # 中间件逻辑
        await self.app(scope, receive, send)

# 在 app/main.py 中注册
app.add_middleware(CustomMiddleware)
```

### 自定义认证策略

```python
# 在 app/auth/ 中实现
class CustomAuthProvider:
    async def authenticate(self, token: str) -> User:
        # 自定义认证逻辑
        pass
    
    async def authorize(self, user: User, resource: str) -> bool:
        # 自定义授权逻辑
        pass
```