#!/bin/bash

# AI功能演示启动脚本

echo "🤖 启动AI功能演示..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 进入项目目录
cd "$(dirname "$0")/.."

echo "📋 1. 启动基础服务..."
cd docker-compose
docker-compose up -d postgres redis rabbitmq neo4j elasticsearch

echo "⏳ 等待数据库服务启动..."
sleep 30

echo "🚀 2. 启动AI Agent服务..."
docker-compose up -d ai-agent-service

echo "⏳ 等待AI服务启动..."
sleep 20

echo "📊 3. 初始化AI演示数据..."

# 添加示例FAQ文档
echo "📄 添加FAQ文档..."
curl -X POST "http://localhost:8004/api/v1/vector/documents/" \
  -H "Content-Type: application/json" \
  -d '{
    "document_type": "faq",
    "title": "如何查询订单状态？",
    "content": "您可以通过以下方式查询订单状态：1. 登录账户，进入我的订单页面；2. 使用订单号在订单查询页面搜索；3. 联系在线客服获取帮助。我们会实时更新订单状态，包括待支付、已支付、已发货、运输中、已送达等状态。",
    "tags": ["订单", "查询", "状态"]
  }' > /dev/null 2>&1

curl -X POST "http://localhost:8004/api/v1/vector/documents/" \
  -H "Content-Type: application/json" \
  -d '{
    "document_type": "faq",
    "title": "支付方式有哪些？",
    "content": "我们支持多种安全便捷的支付方式：1. 支付宝 - 扫码支付或账户余额；2. 微信支付 - 扫码或零钱支付；3. 银行卡支付 - 支持各大银行借记卡和信用卡；4. 货到付款 - 部分地区支持现金或刷卡。所有支付均采用SSL加密，确保资金安全。",
    "tags": ["支付", "方式", "安全"]
  }' > /dev/null 2>&1

curl -X POST "http://localhost:8004/api/v1/vector/documents/" \
  -H "Content-Type: application/json" \
  -d '{
    "document_type": "policy",
    "title": "退款政策说明",
    "content": "退款政策：1. 商品质量问题 - 7天无理由退款；2. 尺寸不合适 - 收到商品7天内可申请退换；3. 商品损坏 - 签收时发现损坏可立即申请退款；4. 退款时效 - 审核通过后1-3个工作日到账。退款金额将原路返回到您的支付账户。",
    "tags": ["退款", "政策", "售后"]
  }' > /dev/null 2>&1

echo "🕸️ 创建知识图谱演示数据..."

# 创建用户节点
curl -X POST "http://localhost:8004/api/v1/knowledge/nodes/" \
  -H "Content-Type: application/json" \
  -d '{
    "node_type": "user",
    "entity_id": "user_demo_001",
    "name": "演示用户张三",
    "properties": {
      "registration_date": "2024-01-15",
      "user_level": "VIP",
      "total_orders": 15,
      "total_spent": 8500.00
    }
  }' > /dev/null 2>&1

# 创建商品节点
curl -X POST "http://localhost:8004/api/v1/knowledge/nodes/" \
  -H "Content-Type: application/json" \
  -d '{
    "node_type": "product",
    "entity_id": "prod_demo_001",
    "name": "iPhone 15 Pro Max",
    "properties": {
      "category": "手机数码",
      "brand": "Apple",
      "price": 9999.00,
      "rating": 4.8
    }
  }' > /dev/null 2>&1

curl -X POST "http://localhost:8004/api/v1/knowledge/nodes/" \
  -H "Content-Type: application/json" \
  -d '{
    "node_type": "product",
    "entity_id": "prod_demo_002",
    "name": "AirPods Pro 2",
    "properties": {
      "category": "手机数码",
      "brand": "Apple",
      "price": 1899.00,
      "rating": 4.7
    }
  }' > /dev/null 2>&1

echo "💬 创建演示聊天会话..."
SESSION_RESPONSE=$(curl -s -X POST "http://localhost:8004/api/v1/chat/sessions/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_demo_001",
    "session_type": "customer_service"
  }')

SESSION_ID=$(echo $SESSION_RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ ! -z "$SESSION_ID" ]; then
    echo "✅ 演示会话创建成功: $SESSION_ID"
else
    echo "⚠️ 会话创建可能失败，请检查服务状态"
fi

echo ""
echo "🎉 AI功能演示环境启动完成！"
echo ""
echo "📊 服务状态检查:"
echo "   AI Agent服务: http://localhost:8004/health"
echo "   API文档: http://localhost:8004/docs"
echo ""
echo "🤖 AI功能演示:"
echo ""
echo "1. 智能客服对话测试:"
echo "   curl -X POST 'http://localhost:8004/api/v1/chat/message/' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"session_id\": \"$SESSION_ID\", \"message\": \"你好，我想查询订单状态\"}'"
echo ""
echo "2. 向量搜索测试:"
echo "   curl -X POST 'http://localhost:8004/api/v1/vector/search/' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"query\": \"如何退款\", \"limit\": 3}'"
echo ""
echo "3. 知识图谱查询:"
echo "   curl 'http://localhost:8004/api/v1/knowledge/nodes/user_demo_001/related'"
echo ""
echo "🌐 管理界面:"
echo "   Neo4j浏览器: http://localhost:7474 (neo4j/password)"
echo "   Elasticsearch: http://localhost:9200"
echo ""
echo "📝 要停止演示环境，运行: docker-compose down"