# Celery 任务管理平台集成

## 🎯 概述

本项目集成了 **Celery + Flower** 作为分布式任务调度和管理平台，提供类似 XXL-JOB 的功能：

- ✅ **分布式任务调度**: 支持多Worker并发执行
- ✅ **任务监控界面**: Flower 提供实时监控
- ✅ **任务管理API**: RESTful API 管理任务
- ✅ **定时任务**: 支持 Cron 表达式
- ✅ **任务队列**: 多队列支持，任务分类执行
- ✅ **故障恢复**: 任务重试和错误处理

## 🏗️ 架构组件

```
┌─────────────────────┐    ┌─────────────────────┐
│   FastAPI Service   │    │    Flower Web UI    │
│   (任务管理API)      │    │   (监控界面)         │
│   Port: 8004        │    │   Port: 5555        │
└─────────────────────┘    └─────────────────────┘
           │                           │
           └───────────┬───────────────┘
                      │
           ┌─────────────────────┐
           │    Redis Broker     │
           │   (消息代理)        │
           │   Port: 6379        │
           └─────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Celery Beat  │ │Celery Worker │ │Celery Worker │
│ (定时调度)   │ │ (任务执行)   │ │ (任务执行)   │
└──────────────┘ └──────────────┘ └──────────────┘
```

## 🚀 快速启动

### 1. 使用 Docker Compose 启动

```bash
cd task-scheduler-service
docker-compose up -d
```

启动的服务：
- **FastAPI 服务**: http://localhost:8004
- **Flower 监控**: http://localhost:5555  
- **Celery Worker**: 后台运行
- **Celery Beat**: 后台运行

### 2. 手动启动（开发环境）

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 Redis (需要预先安装)
redis-server

# 启动 Celery Worker
celery -A celery_app worker --loglevel=info --queues=sync_queue,analysis_queue,default

# 启动 Celery Beat (定时任务调度器)
celery -A celery_app beat --loglevel=info

# 启动 Flower 监控界面
celery -A celery_app flower --port=5555

# 启动 FastAPI 服务
uvicorn app.main:app --host 0.0.0.0 --port 8004
```

### 3. 一键启动脚本

```bash
chmod +x start-celery.sh
./start-celery.sh
```

## 📋 任务管理功能

### 内置任务类型

| 任务名称 | 描述 | 队列 | 调度频率 |
|---------|-----|------|---------|
| `sync_orders` | 订单数据同步 | sync_queue | 每小时 |
| `sync_full_orders` | 全量订单同步 | sync_queue | 每天凌晨2点 |
| `data_analysis` | 数据分析任务 | analysis_queue | 每天凌晨3点 |
| `custom_task` | 自定义任务 | default | 按需执行 |

### API 接口

#### 任务管理
```bash
# 获取 Celery 状态
GET /api/v1/celery/status

# 手动触发订单同步
POST /api/v1/celery/jobs/sync-orders?hours=24

# 手动触发全量同步
POST /api/v1/celery/jobs/sync-full-orders?days=7

# 触发数据分析
POST /api/v1/celery/jobs/data-analysis

# 触发自定义任务
POST /api/v1/celery/jobs/custom
{
  "task_name": "cleanup_logs",
  "params": {"days": 30},
  "queue": "default"
}

# 查看任务状态
GET /api/v1/celery/jobs/{task_id}/status

# 取消任务
POST /api/v1/celery/jobs/{task_id}/cancel
```

#### 监控管理
```bash
# 获取工作节点信息
GET /api/v1/celery/workers

# 获取队列信息
GET /api/v1/celery/queues
```

## 🎛️ Flower 监控界面

访问 http://localhost:5555 查看：

- **任务执行状态**: 实时查看任务执行情况
- **Worker 监控**: 查看工作节点状态和性能
- **任务历史**: 查看任务执行历史和结果
- **队列状态**: 监控队列长度和处理速度
- **系统指标**: CPU、内存、网络使用情况

## ⚙️ 配置说明

### 队列配置
- `sync_queue`: 数据同步任务专用队列
- `analysis_queue`: 数据分析任务专用队列  
- `default`: 默认队列，处理其他任务

### 定时任务配置
在 `celery_app.py` 中的 `beat_schedule` 配置定时任务：

```python
beat_schedule = {
    'task-name': {
        'task': 'app.celery_tasks.task_function',
        'schedule': crontab(hour=2, minute=0),  # 每天凌晨2点
        'options': {'queue': 'queue_name'}
    }
}
```

### 任务超时配置
- `task_time_limit`: 300秒 (硬超时)
- `task_soft_time_limit`: 240秒 (软超时)

## 🔧 自定义任务开发

### 1. 创建任务函数

```python
@celery_app.task(bind=True, name='app.celery_tasks.my_custom_task')
def my_custom_task(self, param1, param2):
    try:
        self.update_state(state='PROGRESS', meta={'status': '任务执行中'})
        
        # 执行任务逻辑
        result = do_something(param1, param2)
        
        return {
            'status': 'SUCCESS',
            'message': '任务完成',
            'data': result
        }
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise
```

### 2. 添加API接口

在 `celery_jobs.py` 中添加对应的API接口来触发任务。

### 3. 配置定时调度

在 `beat_schedule` 中添加定时配置。

## 🚨 监控告警

### 任务失败处理
- 自动重试机制
- 失败任务日志记录
- 错误信息详细追踪

### 性能监控
- 任务执行时间统计
- 队列积压监控
- Worker 健康状态检查

## 🔄 与 XXL-JOB 功能对比

| 功能 | XXL-JOB | Celery + Flower | 状态 |
|------|---------|-----------------|------|
| 任务调度 | ✅ | ✅ | 完全支持 |
| 监控界面 | ✅ | ✅ (Flower) | 完全支持 |
| 分布式执行 | ✅ | ✅ | 完全支持 |
| 任务重试 | ✅ | ✅ | 完全支持 |
| 任务分组 | ✅ | ✅ (队列) | 完全支持 |
| 执行日志 | ✅ | ✅ | 完全支持 |
| 故障转移 | ✅ | ✅ | 完全支持 |
| RESTful API | ✅ | ✅ | 完全支持 |

## 📚 相关文档

- [Celery 官方文档](https://docs.celeryproject.org/)
- [Flower 监控文档](https://flower.readthedocs.io/)
- [Redis 配置指南](https://redis.io/documentation)

