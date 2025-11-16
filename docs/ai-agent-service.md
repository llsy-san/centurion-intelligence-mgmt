# AI智能体服务文档

## 📋 服务概述

AI智能体服务是百夫长智能管理系统的智能化核心，提供智能推荐、数据分析、自动化决策、自然语言处理等AI能力，助力业务智能化升级。

## 🏗️ 服务架构

```
AI请求 → 请求解析 → 模型选择 → AI处理 → 结果返回
   ↓         ↓         ↓         ↓         ↓
 参数验证 → 上下文构建 → 推理计算 → 结果处理 → 缓存存储
 权限检查 → 提示工程 → 模型调用 → 格式化 → 日志记录
```

## 🔧 技术栈

- **框架**: FastAPI 0.104+
- **AI模型**: OpenAI GPT-4, Claude, 本地模型
- **向量数据库**: Chroma, Pinecone
- **机器学习**: scikit-learn, pandas, numpy
- **自然语言处理**: transformers, spaCy
- **缓存**: Redis 7
- **消息队列**: Celery + Redis

## 📊 服务信息

| 属性 | 值 |
|------|-----|
| **服务名称** | ai-agent-service |
| **端口** | 8005 |
| **协议** | HTTP |
| **健康检查** | `/health` |
| **API文档** | `/docs` |
| **数据库表** | ai_sessions, ai_models, knowledge_base |

## 🚀 快速启动

### 使用Docker

```bash
# 启动AI智能体服务
make start-ai

# 或直接使用脚本
./scripts/start-ai-agent-service.sh
```

### 本地开发

```bash
# 进入服务目录
cd ai-agent-service

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload --port 8005
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
  "ai_models": {
    "openai_gpt4": "available",
    "claude": "available",
    "local_llm": "available"
  },
  "vector_db": "connected"
}
```

### 智能对话

#### 创建对话会话
```http
POST /api/v1/ai/chat/sessions
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "user_id": "user123",
  "session_name": "订单咨询",
  "context": {
    "domain": "order_management",
    "user_role": "customer",
    "language": "zh-CN"
  }
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "会话创建成功",
  "data": {
    "session_id": "sess_202411160001",
    "user_id": "user123",
    "session_name": "订单咨询",
    "status": "active",
    "created_at": "2024-11-16T10:00:00Z"
  }
}
```

#### 发送消息
```http
POST /api/v1/ai/chat/sessions/{session_id}/messages
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "message": "我想查询我的订单状态",
  "message_type": "text",
  "context": {
    "order_id": "ORD202411160001",
    "user_intent": "query_order"
  }
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "消息处理成功",
  "data": {
    "message_id": "msg_202411160001",
    "session_id": "sess_202411160001",
    "user_message": "我想查询我的订单状态",
    "ai_response": "您好！我来帮您查询订单状态。您的订单ORD202411160001当前状态是"已发货"，预计明天下午送达。您还需要了解其他信息吗？",
    "response_type": "text",
    "confidence": 0.95,
    "intent": "query_order",
    "entities": [
      {
        "type": "order_id",
        "value": "ORD202411160001",
        "confidence": 0.98
      }
    ],
    "suggestions": [
      "查看物流详情",
      "修改收货地址",
      "联系客服"
    ],
    "timestamp": "2024-11-16T10:01:00Z"
  }
}
```

### 智能推荐

#### 商品推荐
```http
POST /api/v1/ai/recommendations/products
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "user_id": "user123",
  "recommendation_type": "collaborative_filtering",
  "context": {
    "current_product_id": "prod001",
    "category": "electronics",
    "price_range": [100, 500],
    "user_preferences": ["high_quality", "fast_shipping"]
  },
  "limit": 10
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "推荐生成成功",
  "data": {
    "recommendations": [
      {
        "product_id": "prod002",
        "product_name": "智能手机",
        "score": 0.92,
        "reason": "基于您的购买历史和偏好",
        "price": 299.99,
        "category": "electronics",
        "image_url": "https://example.com/product002.jpg"
      },
      {
        "product_id": "prod003",
        "product_name": "无线耳机",
        "score": 0.88,
        "reason": "经常与当前商品一起购买",
        "price": 199.99,
        "category": "electronics",
        "image_url": "https://example.com/product003.jpg"
      }
    ],
    "algorithm": "collaborative_filtering",
    "generated_at": "2024-11-16T10:00:00Z"
  }
}
```

#### 内容推荐
```http
POST /api/v1/ai/recommendations/content
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "user_id": "user123",
  "content_type": "article",
  "context": {
    "current_page": "product_detail",
    "user_interests": ["technology", "shopping"],
    "reading_history": ["tech_review", "buying_guide"]
  },
  "limit": 5
}
```

### 数据分析

#### 销售数据分析
```http
POST /api/v1/ai/analytics/sales
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "analysis_type": "trend_analysis",
  "time_range": {
    "start_date": "2024-11-01",
    "end_date": "2024-11-16"
  },
  "dimensions": ["product_category", "region", "time"],
  "metrics": ["sales_amount", "order_count", "conversion_rate"],
  "filters": {
    "product_category": ["electronics", "clothing"],
    "region": ["beijing", "shanghai"]
  }
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "分析完成",
  "data": {
    "analysis_id": "analysis_202411160001",
    "analysis_type": "trend_analysis",
    "summary": {
      "total_sales": 999999.99,
      "total_orders": 5000,
      "average_order_value": 199.99,
      "growth_rate": 0.15
    },
    "trends": [
      {
        "dimension": "time",
        "trend": "increasing",
        "growth_rate": 0.12,
        "confidence": 0.89
      }
    ],
    "insights": [
      {
        "type": "opportunity",
        "description": "电子产品类别在北京地区销量增长显著，建议加大库存投入",
        "confidence": 0.85,
        "impact": "high"
      }
    ],
    "visualizations": [
      {
        "type": "line_chart",
        "title": "销售趋势图",
        "data_url": "/api/v1/ai/analytics/analysis_202411160001/chart/trend"
      }
    ],
    "generated_at": "2024-11-16T10:00:00Z"
  }
}
```

#### 用户行为分析
```http
POST /api/v1/ai/analytics/user-behavior
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "analysis_type": "user_segmentation",
  "user_ids": ["user123", "user456"],
  "behavior_types": ["browsing", "purchasing", "searching"],
  "time_range": {
    "start_date": "2024-11-01",
    "end_date": "2024-11-16"
  }
}
```

### 智能决策

#### 库存优化建议
```http
POST /api/v1/ai/decisions/inventory-optimization
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "warehouse_id": "WH001",
  "product_categories": ["electronics", "clothing"],
  "optimization_goal": "minimize_cost",
  "constraints": {
    "max_investment": 100000,
    "storage_capacity": 1000,
    "service_level": 0.95
  }
}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "优化建议生成成功",
  "data": {
    "decision_id": "decision_202411160001",
    "optimization_goal": "minimize_cost",
    "recommendations": [
      {
        "product_id": "prod001",
        "current_stock": 50,
        "recommended_stock": 80,
        "action": "increase",
        "reason": "预测需求增长30%",
        "confidence": 0.87,
        "expected_benefit": 5000
      }
    ],
    "summary": {
      "total_investment": 85000,
      "expected_roi": 0.25,
      "risk_level": "low",
      "implementation_priority": "high"
    },
    "generated_at": "2024-11-16T10:00:00Z"
  }
}
```

### 知识库管理

#### 添加知识
```http
POST /api/v1/ai/knowledge
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "title": "订单处理流程",
  "content": "订单处理包括以下步骤：1. 订单验证 2. 库存检查 3. 支付处理 4. 发货安排",
  "category": "business_process",
  "tags": ["order", "process", "workflow"],
  "metadata": {
    "source": "internal_doc",
    "version": "1.0",
    "author": "admin"
  }
}
```

#### 知识检索
```http
GET /api/v1/ai/knowledge/search?query=订单处理&category=business_process&limit=5
Authorization: Bearer <access_token>
```

## 📋 数据模型

### AI会话表 (ai_sessions)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| session_id | VARCHAR(50) | 会话ID |
| user_id | VARCHAR(50) | 用户ID |
| session_name | VARCHAR(200) | 会话名称 |
| status | VARCHAR(20) | 会话状态 |
| context | JSON | 会话上下文 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### AI模型表 (ai_models)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| model_name | VARCHAR(100) | 模型名称 |
| model_type | VARCHAR(50) | 模型类型 |
| version | VARCHAR(20) | 模型版本 |
| status | VARCHAR(20) | 模型状态 |
| config | JSON | 模型配置 |
| performance_metrics | JSON | 性能指标 |
| created_at | TIMESTAMP | 创建时间 |

### 知识库表 (knowledge_base)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| title | VARCHAR(200) | 标题 |
| content | TEXT | 内容 |
| category | VARCHAR(50) | 分类 |
| tags | JSON | 标签 |
| embedding | VECTOR | 向量嵌入 |
| metadata | JSON | 元数据 |
| created_at | TIMESTAMP | 创建时间 |

## 🤖 AI模型集成

### OpenAI GPT-4

```python
# OpenAI配置
OPENAI_CONFIG = {
    "api_key": "your-openai-api-key",
    "model": "gpt-4",
    "max_tokens": 2000,
    "temperature": 0.7,
    "timeout": 30
}

# 使用示例
class OpenAIService:
    async def generate_response(self, prompt: str, context: dict) -> str:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "你是一个智能客服助手"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        return response.choices[0].message.content
```

### 本地模型

```python
# 本地模型配置
LOCAL_MODEL_CONFIG = {
    "model_path": "/models/llama-2-7b-chat",
    "device": "cuda",
    "max_length": 2048,
    "temperature": 0.7
}

# 使用示例
class LocalLLMService:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL_CONFIG["model_path"])
        self.model = AutoModelForCausalLM.from_pretrained(LOCAL_MODEL_CONFIG["model_path"])
    
    async def generate_response(self, prompt: str) -> str:
        inputs = self.tokenizer.encode(prompt, return_tensors="pt")
        outputs = self.model.generate(inputs, max_length=2048, temperature=0.7)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
```

## 🧠 智能算法

### 推荐算法

```python
# 协同过滤推荐
class CollaborativeFiltering:
    def __init__(self):
        self.user_item_matrix = None
        self.similarity_matrix = None
    
    async def train(self, user_item_data: pd.DataFrame):
        """训练推荐模型"""
        self.user_item_matrix = user_item_data.pivot_table(
            index='user_id', 
            columns='item_id', 
            values='rating'
        ).fillna(0)
        
        # 计算用户相似度
        self.similarity_matrix = cosine_similarity(self.user_item_matrix)
    
    async def recommend(self, user_id: str, n_recommendations: int = 10) -> List[dict]:
        """生成推荐"""
        # 实现推荐逻辑
        pass

# 内容推荐
class ContentBasedRecommendation:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        self.item_features = None
    
    async def recommend(self, user_preferences: dict, n_recommendations: int = 10) -> List[dict]:
        """基于内容的推荐"""
        # 实现内容推荐逻辑
        pass
```

### 数据分析算法

```python
# 时间序列分析
class TimeSeriesAnalysis:
    @staticmethod
    async def trend_analysis(data: pd.DataFrame, target_column: str) -> dict:
        """趋势分析"""
        from scipy import stats
        
        # 线性回归分析趋势
        x = np.arange(len(data))
        y = data[target_column].values
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        return {
            "trend": "increasing" if slope > 0 else "decreasing",
            "slope": slope,
            "r_squared": r_value ** 2,
            "p_value": p_value,
            "confidence": 1 - p_value
        }

# 用户分群
class UserSegmentation:
    @staticmethod
    async def kmeans_clustering(user_features: pd.DataFrame, n_clusters: int = 5) -> dict:
        """K-means用户分群"""
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler
        
        # 标准化特征
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(user_features)
        
        # K-means聚类
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(features_scaled)
        
        return {
            "clusters": clusters.tolist(),
            "cluster_centers": kmeans.cluster_centers_.tolist(),
            "inertia": kmeans.inertia_
        }
```

## 🔄 业务流程

### AI对话流程

```mermaid
graph TD
    A[用户发送消息] --> B[意图识别]
    B --> C[实体提取]
    C --> D[上下文理解]
    D --> E[知识检索]
    E --> F[响应生成]
    F --> G[结果优化]
    G --> H[返回响应]
```

### 推荐系统流程

```mermaid
graph TD
    A[用户行为数据] --> B[特征工程]
    B --> C[模型训练]
    C --> D[推荐生成]
    D --> E[结果排序]
    E --> F[多样性优化]
    F --> G[推荐展示]
    G --> H[效果反馈]
    H --> A
```

## 📊 性能监控

### AI模型指标

- **响应时间**: 模型推理的平均响应时间
- **准确率**: 推荐/预测的准确率
- **召回率**: 相关结果的召回比例
- **用户满意度**: 用户对AI服务的满意度评分

### 系统指标

- **API调用量**: 每日AI API调用次数
- **模型使用率**: 各AI模型的使用频率
- **缓存命中率**: AI结果缓存的命中率
- **错误率**: AI服务的错误比例

## 🛠️ 配置说明

### 环境变量

```bash
# 服务配置
AI_SERVICE_HOST=0.0.0.0
AI_SERVICE_PORT=8005
AI_SERVICE_DEBUG=false

# 数据库配置
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/centurion_db

# Redis配置
REDIS_URL=redis://localhost:6379/3

# OpenAI配置
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7

# 本地模型配置
LOCAL_MODEL_PATH=/models/llama-2-7b-chat
LOCAL_MODEL_DEVICE=cuda

# 向量数据库配置
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_COLLECTION=knowledge_base

# 推荐系统配置
RECOMMENDATION_CACHE_TTL=3600
RECOMMENDATION_BATCH_SIZE=100
```

### AI模型配置

```python
# AI模型配置
AI_MODELS = {
    "chat": {
        "primary": "openai_gpt4",
        "fallback": "local_llm",
        "max_tokens": 2000,
        "temperature": 0.7
    },
    "recommendation": {
        "algorithm": "collaborative_filtering",
        "model_path": "/models/recommendation_model.pkl",
        "update_frequency": "daily"
    },
    "analytics": {
        "time_series": "prophet",
        "clustering": "kmeans",
        "classification": "random_forest"
    }
}
```

## 🐛 故障排除

### 常见问题

#### 1. AI模型响应慢
```bash
# 检查模型状态
curl http://localhost:8005/api/v1/ai/models/status

# 查看GPU使用情况
nvidia-smi

# 检查模型缓存
docker exec centurion-redis redis-cli info memory
```

#### 2. 推荐结果不准确
```bash
# 检查训练数据
curl http://localhost:8005/api/v1/ai/recommendations/model-info

# 查看推荐日志
docker logs centurion-ai-service | grep "recommendation"

# 重新训练模型
curl -X POST http://localhost:8005/api/v1/ai/recommendations/retrain
```

#### 3. 知识库检索失败
```bash
# 检查向量数据库
curl http://localhost:8000/api/v1/heartbeat

# 查看知识库状态
curl http://localhost:8005/api/v1/ai/knowledge/status

# 重建索引
curl -X POST http://localhost:8005/api/v1/ai/knowledge/rebuild-index
```