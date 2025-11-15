# 百夫长智能管理系统 - 定时任务服务
## Centurion Intelligence Management System - Task Scheduler Service

## 概述

定时任务服务是百夫长智能管理系统的核心组件，负责从第三方系统获取订单数据并同步到本地数据库，提供订单数据的统一查询接口。

## 主要功能

### 1. 数据同步
- **订单同步**: 从第三方系统获取订单列表并同步到本地数据库
- **订单产品同步**: 获取对账明细和核验记录，同步订单产品信息
- **增量同步**: 支持按时间范围进行增量数据同步
- **全量同步**: 支持全量数据同步和数据修复

### 2. 定时任务
- **每小时同步**: 自动同步最近24小时的订单数据
- **每日全量同步**: 每天凌晨2点执行全量同步任务
- **任务监控**: 提供任务执行状态和日志查询

### 3. 数据查询
- **订单查询**: 提供多维度订单数据查询接口
- **产品查询**: 提供订单产品信息查询接口
- **统计报表**: 提供订单统计和数据分析接口

## 数据模型

### 订单表 (OrderSyncModel)
- `order_no`: 订单编号 (BFZ+年月日+6位自增数字)
- `external_no`: 外部编号 (D开头的来源系统唯一编号)
- `external_order_status`: 外部订单状态
- `order_type`: 订单类型 (WEMINI/APP/OTHER)
- `tenant_id`: 租户ID
- `customer_id`: 客户ID (微信openid)
- `pay_type`: 支付类型 (WECHAT/ALIPAY/OTHER)
- `pay_status`: 支付状态
- `order_status`: 订单状态 (UNPAY/UNUSE/USING/COMPT/REFD/UNDO)

### 订单产品表 (OrderProductSyncModel)
- `order_no`: 关联订单编号
- `external_no`: 外部编号 (m开头)
- `product_id`: 产品ID
- `category_level1-5`: 产品分类层级
- `channel_commission_rate`: 渠道佣金率
- `product_status`: 产品状态
- `verify_method`: 核验方式 (CHECK/FCHECK)
- `refund_status`: 退款状态

## API接口

### 健康检查
```
GET /health
```

### 任务管理
```
GET /api/v1/tasks/status          # 获取调度器状态
POST /api/v1/tasks/sync/orders    # 手动触发订单同步
GET /api/v1/tasks/logs            # 获取任务执行日志
```

### 数据查询
```
GET /api/v1/sync/orders           # 查询订单列表
GET /api/v1/sync/orders/{order_no} # 查询单个订单详情
GET /api/v1/sync/products         # 查询订单产品列表
GET /api/v1/sync/statistics       # 获取统计数据
```

## 部署说明

### 使用Docker部署

1. **构建和启动服务**
```bash
chmod +x start.sh
./start.sh
```

2. **或者手动启动**
```bash
docker-compose build
docker-compose up -d
```

3. **查看服务状态**
```bash
docker-compose ps
docker-compose logs -f task-scheduler-service
```

4. **停止服务**
```bash
docker-compose down
```

### 环境配置

服务支持通过环境变量进行配置：

```bash
# 数据库配置
DATABASE__HOST=localhost
DATABASE__PORT=5432
DATABASE__USERNAME=postgres
DATABASE__PASSWORD=password
DATABASE__DATABASE=order_payment_db

# Redis配置
REDIS__HOST=localhost
REDIS__PORT=6379

# 第三方API配置
THIRD_PARTY_API_URL=https://api.third-party.com
THIRD_PARTY_API_KEY=your-api-key

# 微信支付API配置
WECHAT_PAY_API_URL=https://api.mch.weixin.qq.com
WECHAT_PAY_APP_ID=your-app-id
WECHAT_PAY_MCH_ID=your-mch-id
WECHAT_PAY_API_KEY=your-api-key
```

## 数据同步逻辑

### 订单同步流程
1. 从第三方系统获取订单列表 (list接口)
2. 筛选D开头的order_reference
3. 获取订单详情和微信支付信息
4. 生成本地订单编号 (BFZ格式)
5. 保存/更新订单记录

### 订单产品同步流程
1. 根据外部订单号查询对账明细 (pw_reconciliation_amount_detail)
2. 筛选m开头的order_detail_ind_reference
3. 获取核验记录 (check_record)
4. 解析产品名称中的有效期信息
5. 保存订单产品记录

### 状态映射
- **订单状态**: 根据order_detail中的order_status映射
- **产品状态**: 根据核验记录的use_status确定
- **退款状态**: 根据refund_way字段判断 (0=未退款,1=正常退款,2=强制退款,3=脚本退款)

## 监控和日志

### 任务监控
- 任务执行状态跟踪
- 成功/失败数量统计
- 错误信息记录

### 日志查看
```bash
# 查看实时日志
docker-compose logs -f task-scheduler-service

# 查看特定时间的日志
docker-compose logs --since="2024-01-01T00:00:00" task-scheduler-service
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库配置和网络连接
   - 确认数据库服务已启动

2. **第三方API调用失败**
   - 检查API密钥和URL配置
   - 查看网络连接和防火墙设置

3. **同步任务执行失败**
   - 查看任务日志获取详细错误信息
   - 检查数据格式和业务逻辑

### 调试模式
设置环境变量 `DEBUG=true` 启用调试模式，获取更详细的日志信息。

## 性能优化

- 使用异步数据库操作提高性能
- 批量处理数据减少数据库连接数
- 增量同步减少数据传输量
- 使用连接池管理数据库连接

## 安全考虑

- API密钥通过环境变量配置
- 数据库连接使用加密传输
- 敏感信息不记录到日志中
- 定期更新依赖包修复安全漏洞