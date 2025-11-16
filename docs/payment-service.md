# 支付服务文档

## 📋 服务概述

支付服务是百夫长智能管理系统的核心金融服务，负责处理订单支付、退款、支付回调、账户管理等功能，支持多种支付渠道。

## 🏗️ 服务架构

```
支付请求 → 参数验证 → 渠道路由 → 第三方支付 → 回调处理
    ↓           ↓           ↓           ↓           ↓
  金额校验   →  风控检查  →  支付创建  →  状态同步  → 业务通知
  用户验证   →  限额控制  →  订单绑定  →  结果返回  → 对账处理
```

## 🔧 技术栈

- **框架**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0 (异步)
- **数据库**: PostgreSQL 15
- **缓存**: Redis 7
- **加密**: cryptography
- **HTTP客户端**: httpx (异步)
- **消息队列**: Celery + Redis

## 📊 服务信息

| 属性 | 值 |
|------|-----|
| **服务名称** | payment-service |
| **端口** | 8003 |
| **协议** | HTTP/HTTPS |
| **健康检查** | `/health` |
| **API文档** | `/docs` |
| **数据库表** | payments, payment_logs, refunds |

## 🚀 快速启动

### 使用Docker

```bash
# 启动支付服务
make start-payment

# 或直接使用脚本
./scripts/start-payment-service.sh
```

### 本地开发

```bash
# 进入服务目录
cd payment-service

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload --port 8003
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
  "database": "connected",
  "cache": "connected",
  "payment_channels": {
    "alipay": "available",
    "wechat": "available",
    "unionpay": "available"
  }
}
```

### 支付管理

#### 创建支付
```http
POST /api/v1/payments
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "order_id": "ORD202411160001",
  "amount": 199.98,
  "currency": "CNY",
  "payment_method": "alipay",
  "return_url": "https://example.com/return",
  "notify_url": "https://example.com/notify",
  "description": "订单支付",
  "extra_data": {
    "product_code": "QUICK_WAP_WAY"
  }
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "支付创建成功",
  "data": {
    "payment_id": "PAY202411160001",
    "order_id": "ORD202411160001",
    "amount": 199.98,
    "currency": "CNY",
    "payment_method": "alipay",
    "status": "pending",
    "payment_url": "https://openapi.alipay.com/gateway.do?...",
    "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
    "expires_at": "2024-11-16T11:00:00Z",
    "created_at": "2024-11-16T10:00:00Z"
  }
}
```

#### 查询支付状态
```http
GET /api/v1/payments/{payment_id}
Authorization: Bearer <access_token>
```

**响应示例:**
```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "payment_id": "PAY202411160001",
    "order_id": "ORD202411160001",
    "amount": 199.98,
    "currency": "CNY",
    "payment_method": "alipay",
    "status": "success",
    "transaction_id": "2024111622001234567890123456",
    "paid_at": "2024-11-16T10:05:00Z",
    "created_at": "2024-11-16T10:00:00Z"
  }
}
```

#### 支付回调处理
```http
POST /api/v1/payments/notify/{payment_method}
Content-Type: application/x-www-form-urlencoded

# 支付宝回调参数
app_id=2021000000000000&
method=alipay.trade.wap.pay.return&
charset=UTF-8&
sign_type=RSA2&
sign=xxx&
timestamp=2024-11-16+10:05:00&
version=1.0&
out_trade_no=PAY202411160001&
trade_no=2024111622001234567890123456&
trade_status=TRADE_SUCCESS&
total_amount=199.98
```

#### 申请退款
```http
POST /api/v1/payments/{payment_id}/refund
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "refund_amount": 199.98,
  "refund_reason": "用户申请退款",
  "notify_url": "https://example.com/refund_notify"
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "退款申请成功",
  "data": {
    "refund_id": "REF202411160001",
    "payment_id": "PAY202411160001",
    "refund_amount": 199.98,
    "refund_reason": "用户申请退款",
    "status": "processing",
    "created_at": "2024-11-16T10:30:00Z"
  }
}
```

### 支付渠道管理

#### 获取支付渠道列表
```http
GET /api/v1/payments/channels
Authorization: Bearer <access_token>
```

**响应示例:**
```json
{
  "code": 200,
  "message": "查询成功",
  "data": [
    {
      "channel": "alipay",
      "name": "支付宝",
      "status": "enabled",
      "fee_rate": 0.006,
      "min_amount": 0.01,
      "max_amount": 50000.00,
      "supported_currencies": ["CNY"]
    },
    {
      "channel": "wechat",
      "name": "微信支付",
      "status": "enabled",
      "fee_rate": 0.006,
      "min_amount": 0.01,
      "max_amount": 50000.00,
      "supported_currencies": ["CNY"]
    }
  ]
}
```

### 支付统计

#### 支付统计信息
```http
GET /api/v1/payments/statistics?start_date=2024-11-01&end_date=2024-11-16
Authorization: Bearer <access_token>
```

**响应示例:**
```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "total_payments": 1000,
    "total_amount": 199999.99,
    "success_rate": 0.95,
    "channel_distribution": {
      "alipay": {
        "count": 600,
        "amount": 119999.99
      },
      "wechat": {
        "count": 400,
        "amount": 80000.00
      }
    },
    "daily_statistics": [
      {
        "date": "2024-11-16",
        "payments": 50,
        "amount": 9999.99,
        "success_rate": 0.96
      }
    ]
  }
}
```

## 📋 数据模型

### 支付表 (payments)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| payment_id | VARCHAR(50) | 支付单号 |
| order_id | VARCHAR(50) | 订单ID |
| user_id | VARCHAR(50) | 用户ID |
| amount | DECIMAL(10,2) | 支付金额 |
| currency | VARCHAR(3) | 货币类型 |
| payment_method | VARCHAR(20) | 支付方式 |
| status | VARCHAR(20) | 支付状态 |
| transaction_id | VARCHAR(100) | 第三方交易号 |
| return_url | VARCHAR(500) | 返回地址 |
| notify_url | VARCHAR(500) | 通知地址 |
| description | VARCHAR(200) | 支付描述 |
| extra_data | JSON | 扩展数据 |
| paid_at | TIMESTAMP | 支付时间 |
| expires_at | TIMESTAMP | 过期时间 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### 退款表 (refunds)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| refund_id | VARCHAR(50) | 退款单号 |
| payment_id | VARCHAR(50) | 支付单号 |
| refund_amount | DECIMAL(10,2) | 退款金额 |
| refund_reason | VARCHAR(200) | 退款原因 |
| status | VARCHAR(20) | 退款状态 |
| refund_transaction_id | VARCHAR(100) | 第三方退款号 |
| notify_url | VARCHAR(500) | 通知地址 |
| processed_at | TIMESTAMP | 处理时间 |
| created_at | TIMESTAMP | 创建时间 |

### 支付日志表 (payment_logs)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| payment_id | VARCHAR(50) | 支付单号 |
| action | VARCHAR(50) | 操作类型 |
| request_data | JSON | 请求数据 |
| response_data | JSON | 响应数据 |
| status_code | INTEGER | 状态码 |
| error_message | TEXT | 错误信息 |
| created_at | TIMESTAMP | 创建时间 |

### 支付状态

| 状态 | 说明 |
|------|------|
| **pending** | 待支付 |
| **processing** | 支付中 |
| **success** | 支付成功 |
| **failed** | 支付失败 |
| **cancelled** | 已取消 |
| **expired** | 已过期 |
| **refunded** | 已退款 |

## 💳 支付渠道

### 支付宝 (Alipay)

```python
# 支付宝配置
ALIPAY_CONFIG = {
    "app_id": "2021000000000000",
    "private_key": "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...",
    "public_key": "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuWJKrQ6SWvS9...",
    "gateway": "https://openapi.alipay.com/gateway.do",
    "sign_type": "RSA2",
    "charset": "UTF-8",
    "version": "1.0"
}

# 支持的支付方式
ALIPAY_METHODS = [
    "alipay.trade.page.pay",      # 电脑网站支付
    "alipay.trade.wap.pay",       # 手机网站支付
    "alipay.trade.app.pay",       # APP支付
    "alipay.trade.precreate"      # 扫码支付
]
```

### 微信支付 (WeChat Pay)

```python
# 微信支付配置
WECHAT_CONFIG = {
    "app_id": "wx1234567890123456",
    "mch_id": "1234567890",
    "api_key": "your_api_key_32_characters_long",
    "cert_path": "/path/to/apiclient_cert.pem",
    "key_path": "/path/to/apiclient_key.pem",
    "gateway": "https://api.mch.weixin.qq.com",
    "notify_url": "https://your-domain.com/api/v1/payments/notify/wechat"
}

# 支持的支付方式
WECHAT_METHODS = [
    "JSAPI",    # 公众号支付
    "NATIVE",   # 扫码支付
    "APP",      # APP支付
    "MWEB"      # H5支付
]
```

### 银联支付 (UnionPay)

```python
# 银联支付配置
UNIONPAY_CONFIG = {
    "mer_id": "123456789012345",
    "private_key": "path/to/private.key",
    "public_key": "path/to/public.key",
    "gateway": "https://gateway.95516.com",
    "version": "5.1.0",
    "encoding": "UTF-8"
}
```

## 🔐 安全机制

### 数据加密

```python
# 敏感数据加密
from cryptography.fernet import Fernet

class PaymentEncryption:
    def __init__(self, key: str):
        self.cipher = Fernet(key.encode())
    
    def encrypt_card_info(self, card_info: dict) -> str:
        """加密银行卡信息"""
        data = json.dumps(card_info).encode()
        return self.cipher.encrypt(data).decode()
    
    def decrypt_card_info(self, encrypted_data: str) -> dict:
        """解密银行卡信息"""
        data = self.cipher.decrypt(encrypted_data.encode())
        return json.loads(data.decode())
```

### 签名验证

```python
# 支付回调签名验证
class SignatureValidator:
    @staticmethod
    def verify_alipay_signature(params: dict, signature: str) -> bool:
        """验证支付宝签名"""
        # 实现支付宝签名验证逻辑
        pass
    
    @staticmethod
    def verify_wechat_signature(params: dict, signature: str) -> bool:
        """验证微信支付签名"""
        # 实现微信支付签名验证逻辑
        pass
```

### 风控检查

```python
# 支付风控
class PaymentRiskControl:
    @staticmethod
    async def check_payment_risk(payment_data: dict) -> dict:
        """支付风险检查"""
        risk_score = 0
        risk_factors = []
        
        # 金额风险检查
        if payment_data["amount"] > 10000:
            risk_score += 30
            risk_factors.append("大额支付")
        
        # 频次风险检查
        recent_payments = await get_recent_payments(
            payment_data["user_id"], 
            minutes=10
        )
        if len(recent_payments) > 5:
            risk_score += 50
            risk_factors.append("高频支付")
        
        return {
            "risk_score": risk_score,
            "risk_level": "high" if risk_score > 70 else "medium" if risk_score > 30 else "low",
            "risk_factors": risk_factors,
            "allow_payment": risk_score < 80
        }
```

## 🔄 业务流程

### 支付流程

```mermaid
graph TD
    A[创建支付请求] --> B[参数验证]
    B --> C[风控检查]
    C --> D[选择支付渠道]
    D --> E[调用第三方支付]
    E --> F[返回支付信息]
    F --> G[用户完成支付]
    G --> H[接收支付回调]
    H --> I[验证回调签名]
    I --> J[更新支付状态]
    J --> K[通知业务系统]
```

### 退款流程

```mermaid
graph TD
    A[申请退款] --> B[验证退款条件]
    B --> C[创建退款记录]
    C --> D[调用第三方退款]
    D --> E[处理退款结果]
    E --> F[更新退款状态]
    F --> G[通知用户]
```

## 📊 监控指标

### 支付指标

- **支付成功率**: 成功支付数 / 总支付数
- **平均支付时间**: 从创建到完成的平均时间
- **渠道成功率**: 各支付渠道的成功率
- **退款率**: 退款金额 / 支付金额

### 性能指标

- **API响应时间**: P50、P95、P99响应时间
- **第三方调用延迟**: 各支付渠道的调用延迟
- **错误率**: 4xx、5xx错误比例
- **并发处理能力**: 每秒处理的支付请求数

## 🛠️ 配置说明

### 环境变量

```bash
# 服务配置
PAYMENT_SERVICE_HOST=0.0.0.0
PAYMENT_SERVICE_PORT=8003
PAYMENT_SERVICE_DEBUG=false

# 数据库配置
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/centurion_db

# Redis配置
REDIS_URL=redis://localhost:6379/1

# 支付宝配置
ALIPAY_APP_ID=2021000000000000
ALIPAY_PRIVATE_KEY=path/to/alipay_private_key.pem
ALIPAY_PUBLIC_KEY=path/to/alipay_public_key.pem
ALIPAY_GATEWAY=https://openapi.alipay.com/gateway.do

# 微信支付配置
WECHAT_APP_ID=wx1234567890123456
WECHAT_MCH_ID=1234567890
WECHAT_API_KEY=your_api_key_32_characters_long
WECHAT_CERT_PATH=path/to/apiclient_cert.pem
WECHAT_KEY_PATH=path/to/apiclient_key.pem

# 加密配置
PAYMENT_ENCRYPTION_KEY=your-32-character-encryption-key
```

### 支付渠道配置

```python
# 支付渠道配置
PAYMENT_CHANNELS = {
    "alipay": {
        "enabled": True,
        "fee_rate": 0.006,
        "min_amount": 0.01,
        "max_amount": 50000.00,
        "timeout": 30,
        "retry_times": 3
    },
    "wechat": {
        "enabled": True,
        "fee_rate": 0.006,
        "min_amount": 0.01,
        "max_amount": 50000.00,
        "timeout": 30,
        "retry_times": 3
    },
    "unionpay": {
        "enabled": False,
        "fee_rate": 0.008,
        "min_amount": 0.01,
        "max_amount": 100000.00,
        "timeout": 60,
        "retry_times": 2
    }
}
```

## 🐛 故障排除

### 常见问题

#### 1. 支付创建失败
```bash
# 检查支付渠道配置
curl http://localhost:8003/api/v1/payments/channels

# 查看服务日志
docker logs centurion-payment-service

# 检查第三方服务连通性
curl -I https://openapi.alipay.com/gateway.do
```

#### 2. 支付回调处理失败
```bash
# 检查回调URL配置
echo $PAYMENT_NOTIFY_URL

# 查看回调日志
docker logs centurion-payment-service | grep "notify"

# 验证签名配置
curl -X POST http://localhost:8003/api/v1/payments/test-signature
```

#### 3. 退款处理失败
```bash
# 检查退款权限
curl -H "Authorization: Bearer <token>" http://localhost:8003/api/v1/payments/test/refund

# 查看退款日志
docker logs centurion-payment-service | grep "refund"

# 检查第三方退款接口
curl -I https://openapi.alipay.com/gateway.do
```

### 日志分析

```bash
# 查看支付创建日志
docker logs centurion-payment-service | grep "payment_created"

# 查看支付成功日志
docker logs centurion-payment-service | grep "payment_success"

# 查看错误日志
docker logs centurion-payment-service | grep ERROR
```