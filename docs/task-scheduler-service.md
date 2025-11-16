# 任务调度服务文档

## 📋 服务概述

任务调度服务是百夫长智能管理系统的核心基础设施，负责定时任务、异步任务、批量处理、工作流调度等功能，基于Celery和Flower构建。

## 🏗️ 服务架构

```
任务请求 → 任务验证 → 队列分发 → 工作节点 → 结果处理
    ↓           ↓           ↓           ↓           ↓
  参数校验   →  调度策略  →  负载均衡  →  任务执行  → 状态更新
  权限检查   →  优先级   →  资源分配  →  错误处理  → 结果存储
```

## 🔧 技术栈

- **任务队列**: Celery 5.3+
- **消息代理**: Redis 7
- **结果后端**: Redis 7
- **监控界面**: Flower
- **框架**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0 (异步)
- **数据库**: PostgreSQL 15

## 📊 服务信息

| 属性 | 值 |
|------|-----|
| **服务名称** | task-scheduler-service |
| **端口** | 8006 |
| **协议** | HTTP |
| **健康检查** | `/health` |
| **API文档** | `/docs` |
| **Flower监控** | `http://localhost:5555` |
| **数据库表** | tasks, task_schedules, task_logs |

## 🚀 快速启动

### 使用Docker

```bash
# 启动任务调度服务
make start-task

# 或直接使用脚本
./scripts/start-task-scheduler-service.sh
```

### 本地开发

```bash
# 进入服务目录
cd task-scheduler-service

# 安装依赖
pip install -r requirements.txt

# 启动Celery Worker
celery -A app.celery worker --loglevel=info

# 启动Celery Beat (定时任务)
celery -A app.celery beat --loglevel=info

# 启动Flower监控
celery -A app.celery flower --port=5555

# 启动API服务
uvicorn app.main:app --reload --port 8006
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
  "redis": "connected",
  "celery": {
    "active_workers": 3,
    "active_tasks": 5,
    "scheduled_tasks": 10
  },
  "flower": "running"
}
```

### 任务管理

#### 创建异步任务
```http
POST /api/v1/tasks
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "task_name": "send_email",
  "task_type": "async",
  "parameters": {
    "to": "user@example.com",
    "subject": "订单确认",
    "template": "order_confirmation",
    "data": {
      "order_id": "ORD202411160001",
      "amount": 199.98
    }
  },
  "priority": "normal",
  "retry_count": 3,
  "timeout": 300,
  "queue": "email"
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "任务创建成功",
  "data": {
    "task_id": "task_202411160001",
    "celery_task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "task_name": "send_email",
    "status": "pending",
    "priority": "normal",
    "queue": "email",
    "created_at": "2024-11-16T10:00:00Z",
    "estimated_completion": "2024-11-16T10:05:00Z"
  }
}
```

#### 查询任务状态
```http
GET /api/v1/tasks/{task_id}
Authorization: Bearer <access_token>
```

#### 创建定时任务
```http
POST /api/v1/schedules
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "schedule_name": "daily_report",
  "task_name": "generate_daily_report",
  "schedule_type": "cron",
  "schedule_expression": "0 9 * * *",
  "parameters": {
    "report_type": "sales",
    "recipients": ["admin@example.com"]
  },
  "timezone": "Asia/Shanghai",
  "enabled": true,
  "max_instances": 1
}
```

## 📋 数据模型

### 任务表 (tasks)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| task_id | VARCHAR(50) | 任务ID |
| celery_task_id | VARCHAR(100) | Celery任务ID |
| task_name | VARCHAR(100) | 任务名称 |
| task_type | VARCHAR(20) | 任务类型 |
| status | VARCHAR(20) | 任务状态 |
| parameters | JSON | 任务参数 |
| result | JSON | 执行结果 |
| error | TEXT | 错误信息 |
| priority | VARCHAR(20) | 优先级 |
| queue | VARCHAR(50) | 队列名称 |
| retry_count | INTEGER | 重试次数 |
| max_retries | INTEGER | 最大重试次数 |
| timeout | INTEGER | 超时时间(秒) |
| started_at | TIMESTAMP | 开始时间 |
| completed_at | TIMESTAMP | 完成时间 |
| created_at | TIMESTAMP | 创建时间 |

### 任务状态

| 状态 | 说明 |
|------|------|
| **pending** | 等待执行 |
| **started** | 正在执行 |
| **retry** | 重试中 |
| **success** | 执行成功 |
| **failure** | 执行失败 |
| **revoked** | 已撤销 |
| **timeout** | 执行超时 |

## 🔧 任务定义

### 邮件发送任务

```python
from celery import Task
from app.celery import celery_app

@celery_app.task(bind=True, name="send_email")
def send_email(self: Task, to: str, subject: str, template: str, data: dict):
    """发送邮件任务"""
    try:
        # 更新任务进度
        self.update_state(state='PROGRESS', meta={'progress': 10})
        
        # 渲染邮件模板
        email_content = render_email_template(template, data)
        self.update_state(state='PROGRESS', meta={'progress': 50})
        
        # 发送邮件
        message_id = send_email_via_smtp(to, subject, email_content)
        self.update_state(state='PROGRESS', meta={'progress': 100})
        
        return {
            'message_id': message_id,
            'sent_at': datetime.now().isoformat()
        }
    except Exception as exc:
        # 记录错误并重试
        self.retry(exc=exc, countdown=60, max_retries=3)
```

## ⏰ 调度配置

### Cron表达式

```python
# 定时任务配置
CELERY_BEAT_SCHEDULE = {
    # 每天上午9点生成日报
    'daily-report': {
        'task': 'generate_daily_report',
        'schedule': crontab(hour=9, minute=0),
        'args': ('sales',),
        'options': {'queue': 'reports'}
    },
    
    # 每小时同步库存
    'sync-inventory': {
        'task': 'sync_inventory_data',
        'schedule': crontab(minute=0),
        'options': {'queue': 'sync'}
    }
}
```

## 🛠️ 配置说明

### 环境变量

```bash
# 服务配置
TASK_SERVICE_HOST=0.0.0.0
TASK_SERVICE_PORT=8006
TASK_SERVICE_DEBUG=false

# 数据库配置
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/centurion_db

# Redis配置
REDIS_URL=redis://localhost:6379/4
CELERY_BROKER_URL=redis://localhost:6379/4
CELERY_RESULT_BACKEND=redis://localhost:6379/4

# Flower配置
FLOWER_PORT=5555
FLOWER_BASIC_AUTH=admin:password
```

## 🐛 故障排除

### 常见问题

#### 1. 任务执行失败
```bash
# 检查Celery Worker状态
celery -A app.celery inspect active

# 查看任务日志
docker logs centurion-task-scheduler

# 检查Redis连接
docker exec centurion-redis redis-cli ping
```

#### 2. 定时任务不执行
```bash
# 检查Celery Beat状态
celery -A app.celery inspect scheduled

# 查看Beat日志
docker logs centurion-celery-beat

# 检查时区配置
echo $CELERY_TIMEZONE
```

## 📚 相关文档

- [项目概览](project-overview.md)
- [部署指南](deployment.md)
- [API网关服务](api-gateway.md)
- [订单服务](order-service.md)
- [支付服务](payment-service.md)
- [物流服务](shipping-service.md)
- [AI智能体服务](ai-agent-service.md)

## 📞 技术支持

如遇到任务调度服务相关问题，请：

1. 查看服务日志
2. 检查Celery配置
3. 验证Redis连接
4. 联系技术支持团队