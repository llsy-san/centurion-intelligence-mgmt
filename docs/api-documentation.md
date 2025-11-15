# API 接口文档

## 认证说明

所有API接口（除登录接口外）都需要在请求头中携带JWT Token：

```
Authorization: Bearer <your-jwt-token>
```

## 获取Token

### 用户登录
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password"
}
```

响应：
```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

## 订单相关API

### 创建订单
```http
POST /api/v1/orders/
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_id": "user_001",
  "items": [
    {
      "product_id": "prod_001",
      "product_name": "商品1",
      "quantity": 2,
      "unit_price": 99.99,
      "total_price": 199.98
    }
  ],
  "shipping_address": "北京市朝阳区xxx街道xxx号",
  "phone": "13800138000",
  "notes": "订单备注"
}
```

### 获取订单详情
```http
GET /api/v1/orders/{order_id}
Authorization: Bearer <token>
```

### 获取用户订单列表
```http
GET /api/v1/orders/user/{user_id}?skip=0&limit=10
Authorization: Bearer <token>
```

### 更新订单状态
```http
PUT /api/v1/orders/{order_id}/status
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "confirmed"
}
```

### 取消订单
```http
PUT /api/v1/orders/{order_id}/cancel
Authorization: Bearer <token>
```

## 支付相关API

### 创建支付
```http
POST /api/v1/payments/
Authorization: Bearer <token>
Content-Type: application/json

{
  "order_id": "ORD20241028001",
  "amount": 199.98,
  "payment_method": "alipay"
}
```

### 获取支付详情
```http
GET /api/v1/payments/{payment_id}
Authorization: Bearer <token>
```

### 根据订单获取支付
```http
GET /api/v1/payments/order/{order_id}
Authorization: Bearer <token>
```

### 处理支付
```http
POST /api/v1/payments/{payment_id}/process
Authorization: Bearer <token>
```

### 退款
```http
POST /api/v1/payments/{payment_id}/refund
Authorization: Bearer <token>
```

## 发货相关API

### 创建发货记录
```http
POST /api/v1/shipping/
Authorization: Bearer <token>
Content-Type: application/json

{
  "order_id": "ORD20241028001",
  "shipping_address": "北京市朝阳区xxx街道xxx号",
  "phone": "13800138000"
}
```

### 获取发货详情
```http
GET /api/v1/shipping/{shipping_id}
Authorization: Bearer <token>
```

### 根据订单获取发货信息
```http
GET /api/v1/shipping/order/{order_id}
Authorization: Bearer <token>
```

### 根据快递单号追踪
```http
GET /api/v1/shipping/track/{tracking_number}
Authorization: Bearer <token>
```

### 更新发货状态
```http
PUT /api/v1/shipping/{shipping_id}/status
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "shipped",
  "tracking_number": "SF20241028001",
  "carrier": "顺丰速运"
}
```

## 系统API

### 健康检查
```http
GET /health
```

### 获取系统信息
```http
GET /api/v1/system/info
Authorization: Bearer <token>
```

## 状态码说明

- `pending`: 待处理
- `confirmed`: 已确认
- `paid`: 已支付
- `shipped`: 已发货
- `delivered`: 已送达
- `cancelled`: 已取消
- `refunded`: 已退款

## 错误响应格式

```json
{
  "success": false,
  "message": "错误描述",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-10-28T12:00:00"
}
```

## 常见错误码

- `INVALID_TOKEN`: 无效的访问令牌
- `ORDER_NOT_FOUND`: 订单不存在
- `PAYMENT_FAILED`: 支付失败
- `SHIPPING_FAILED`: 发货失败
- `RATE_LIMIT_EXCEEDED`: 请求频率超限