"""
AI Agent服务业务逻辑
提供知识图谱构建、向量搜索、智能对话等功能
集成Milvus高性能向量数据库
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Dict, Any, Optional, Tuple
import json
import numpy as np
from datetime import datetime
import httpx
import asyncio

from .database import (
    KnowledgeNodeModel, KnowledgeRelationModel, 
    VectorDocumentModel, ChatSessionModel, ChatMessageModel
)
from .milvus_service import milvus_service


class EmbeddingService:
    """向量嵌入服务"""
    
    def __init__(self):
        self.model_name = "text-embedding-ada-002"
        self.api_key = "your-openai-api-key"  # 实际使用时从环境变量获取
    
    async def get_embedding(self, text: str) -> List[float]:
        """获取文本的向量嵌入"""
        try:
            # 模拟OpenAI API调用
            # 实际使用时替换为真实的API调用
            return self._mock_embedding(text)
        except Exception as e:
            print(f"获取嵌入向量失败: {e}")
            return self._mock_embedding(text)
    
    def _mock_embedding(self, text: str) -> List[float]:
        """模拟嵌入向量生成"""
        # 简单的哈希基础向量生成（仅用于演示）
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_hex = hash_obj.hexdigest()
        
        # 生成1536维向量（OpenAI embedding维度）
        np.random.seed(int(hash_hex[:8], 16))
        embedding = np.random.normal(0, 1, 1536).tolist()
        return embedding
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)


class KnowledgeGraphService:
    """知识图谱服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_service = EmbeddingService()
    
    async def create_node(
        self, 
        node_type: str, 
        entity_id: str, 
        name: str, 
        properties: Dict[str, Any]
    ) -> KnowledgeNodeModel:
        """创建知识图谱节点"""
        # 生成节点描述文本用于嵌入
        description = f"{node_type}: {name} {json.dumps(properties, ensure_ascii=False)}"
        embedding = await self.embedding_service.get_embedding(description)
        
        node = KnowledgeNodeModel(
            node_type=node_type,
            entity_id=entity_id,
            name=name,
            properties=properties,
            embedding=json.dumps(embedding)
        )
        
        self.db.add(node)
        await self.db.commit()
        await self.db.refresh(node)
        return node
    
    async def create_relation(
        self,
        source_node_id: str,
        target_node_id: str,
        relation_type: str,
        properties: Dict[str, Any] = None,
        weight: float = 1.0
    ) -> KnowledgeRelationModel:
        """创建知识图谱关系"""
        relation = KnowledgeRelationModel(
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            relation_type=relation_type,
            properties=properties or {},
            weight=weight
        )
        
        self.db.add(relation)
        await self.db.commit()
        await self.db.refresh(relation)
        return relation
    
    async def find_related_nodes(
        self, 
        node_id: str, 
        relation_types: List[str] = None,
        max_depth: int = 2
    ) -> List[Dict[str, Any]]:
        """查找相关节点"""
        # 构建查询条件
        conditions = [
            or_(
                KnowledgeRelationModel.source_node_id == node_id,
                KnowledgeRelationModel.target_node_id == node_id
            )
        ]
        
        if relation_types:
            conditions.append(KnowledgeRelationModel.relation_type.in_(relation_types))
        
        # 执行查询
        query = select(KnowledgeRelationModel).where(and_(*conditions))
        result = await self.db.execute(query)
        relations = result.scalars().all()
        
        # 获取相关节点信息
        related_nodes = []
        for relation in relations:
            related_node_id = (
                relation.target_node_id if relation.source_node_id == node_id 
                else relation.source_node_id
            )
            
            node_query = select(KnowledgeNodeModel).where(
                KnowledgeNodeModel.id == related_node_id
            )
            node_result = await self.db.execute(node_query)
            node = node_result.scalar_one_or_none()
            
            if node:
                related_nodes.append({
                    "node": {
                        "id": str(node.id),
                        "type": node.node_type,
                        "entity_id": node.entity_id,
                        "name": node.name,
                        "properties": node.properties
                    },
                    "relation": {
                        "type": relation.relation_type,
                        "properties": relation.properties,
                        "weight": relation.weight
                    }
                })
        
        return related_nodes
    
    async def build_order_knowledge_graph(self, order_data: Dict[str, Any]):
        """构建订单相关的知识图谱"""
        try:
            # 创建订单节点
            order_node = await self.create_node(
                node_type="order",
                entity_id=order_data["id"],
                name=f"订单 {order_data['id']}",
                properties={
                    "total_amount": order_data.get("total_amount"),
                    "status": order_data.get("status"),
                    "created_at": order_data.get("created_at")
                }
            )
            
            # 创建用户节点
            user_node = await self.create_node(
                node_type="user",
                entity_id=order_data["user_id"],
                name=f"用户 {order_data['user_id']}",
                properties={}
            )
            
            # 创建订单-用户关系
            await self.create_relation(
                source_node_id=str(order_node.id),
                target_node_id=str(user_node.id),
                relation_type="belongs_to",
                properties={"created_at": datetime.now().isoformat()}
            )
            
            # 创建商品节点和关系
            for item in order_data.get("items", []):
                product_node = await self.create_node(
                    node_type="product",
                    entity_id=item["product_id"],
                    name=item["product_name"],
                    properties={
                        "unit_price": item.get("unit_price"),
                        "category": item.get("category")
                    }
                )
                
                # 创建订单-商品关系
                await self.create_relation(
                    source_node_id=str(order_node.id),
                    target_node_id=str(product_node.id),
                    relation_type="contains",
                    properties={
                        "quantity": item.get("quantity"),
                        "total_price": item.get("total_price")
                    }
                )
            
            return {"status": "success", "order_node_id": str(order_node.id)}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}


class MilvusVectorSearchService:
    """基于Milvus的高性能向量搜索服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_service = EmbeddingService()
    
    async def add_document(
        self,
        document_type: str,
        title: str,
        content: str,
        metadata: Dict[str, Any] = None,
        tags: List[str] = None
    ) -> VectorDocumentModel:
        """添加文档到向量数据库"""
        # 生成文档嵌入
        full_text = f"{title} {content}"
        embedding = await self.embedding_service.get_embedding(full_text)
        
        # 保存到PostgreSQL
        document = VectorDocumentModel(
            document_type=document_type,
            title=title,
            content=content,
            metadata=metadata or {},
            embedding=json.dumps(embedding),
            tags=tags or []
        )
        
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        
        # 同时保存到Milvus
        try:
            milvus_metadata = {
                "document_id": str(document.id),
                "document_type": document_type,
                "title": title,
                "tags": tags or [],
                **(metadata or {})
            }
            
            await milvus_service.batch_insert_documents([{
                "document_id": str(document.id),
                "embedding": embedding,
                "metadata": milvus_metadata
            }])
        except Exception as e:
            print(f"保存到Milvus失败: {e}")
        
        return document
    
    async def search_similar_documents(
        self,
        query: str,
        document_types: List[str] = None,
        limit: int = 5,
        similarity_threshold: float = 0.7,
        use_milvus: bool = True
    ) -> List[Dict[str, Any]]:
        """搜索相似文档"""
        # 生成查询嵌入
        query_embedding = await self.embedding_service.get_embedding(query)
        
        if use_milvus:
            # 使用Milvus进行高性能搜索
            try:
                milvus_results = await milvus_service.search_similar_documents(
                    query_embedding=query_embedding,
                    document_types=document_types,
                    top_k=limit
                )
                
                # 格式化Milvus结果
                formatted_results = []
                for hit in milvus_results:
                    if hit["score"] >= similarity_threshold:
                        entity_data = hit.get("entity", {})
                        metadata = entity_data.get("metadata", {})
                        
                        formatted_results.append({
                            "document": {
                                "id": metadata.get("document_id"),
                                "type": metadata.get("document_type"),
                                "title": metadata.get("title"),
                                "content": "",  # 从PostgreSQL获取完整内容
                                "metadata": metadata,
                                "tags": metadata.get("tags", [])
                            },
                            "similarity": hit["score"]
                        })
                
                # 从PostgreSQL获取完整文档内容
                for result in formatted_results:
                    doc_id = result["document"]["id"]
                    if doc_id:
                        query_stmt = select(VectorDocumentModel).where(
                            VectorDocumentModel.id == doc_id
                        )
                        db_result = await self.db.execute(query_stmt)
                        doc = db_result.scalar_one_or_none()
                        if doc:
                            result["document"]["content"] = doc.content
                
                return formatted_results
                
            except Exception as e:
                print(f"Milvus搜索失败，回退到PostgreSQL: {e}")
        
        # 回退到PostgreSQL搜索
        return await self._search_with_postgresql(
            query_embedding, document_types, limit, similarity_threshold
        )
    
    async def _search_with_postgresql(
        self,
        query_embedding: List[float],
        document_types: List[str] = None,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """使用PostgreSQL进行向量搜索（回退方案）"""
        # 构建查询条件
        conditions = []
        if document_types:
            conditions.append(VectorDocumentModel.document_type.in_(document_types))
        
        # 获取所有文档
        if conditions:
            query_stmt = select(VectorDocumentModel).where(and_(*conditions))
        else:
            query_stmt = select(VectorDocumentModel)
        
        result = await self.db.execute(query_stmt)
        documents = result.scalars().all()
        
        # 计算相似度并排序
        similarities = []
        for doc in documents:
            doc_embedding = json.loads(doc.embedding)
            similarity = self.embedding_service.cosine_similarity(
                query_embedding, doc_embedding
            )
            
            if similarity >= similarity_threshold:
                similarities.append({
                    "document": {
                        "id": str(doc.id),
                        "type": doc.document_type,
                        "title": doc.title,
                        "content": doc.content,
                        "metadata": doc.metadata,
                        "tags": doc.tags
                    },
                    "similarity": similarity
                })
        
        # 按相似度排序并返回前N个
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return similarities[:limit]
    
    async def add_product_vector(
        self,
        product_id: str,
        product_name: str,
        description: str,
        category: str,
        price: float,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """添加商品向量到Milvus"""
        try:
            # 生成商品描述向量
            product_text = f"{product_name} {description} {category}"
            embedding = await self.embedding_service.get_embedding(product_text)
            
            # 准备元数据
            milvus_metadata = {
                "product_id": product_id,
                "name": product_name,
                "category": category,
                "price": price,
                **(metadata or {})
            }
            
            # 插入到Milvus
            await milvus_service.batch_insert_products([{
                "product_id": product_id,
                "embedding": embedding,
                "metadata": milvus_metadata
            }])
            
            return True
        except Exception as e:
            print(f"添加商品向量失败: {e}")
            return False
    
    async def search_similar_products(
        self,
        query: str,
        categories: List[str] = None,
        price_range: Tuple[float, float] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """搜索相似商品"""
        try:
            # 生成查询向量
            query_embedding = await self.embedding_service.get_embedding(query)
            
            # 使用Milvus搜索
            results = await milvus_service.search_similar_products(
                query_embedding=query_embedding,
                categories=categories,
                price_range=price_range,
                top_k=limit
            )
            
            # 格式化结果
            formatted_results = []
            for hit in results:
                entity_data = hit.get("entity", {})
                metadata = entity_data.get("metadata", {})
                
                formatted_results.append({
                    "product": {
                        "id": metadata.get("product_id"),
                        "name": metadata.get("name"),
                        "category": metadata.get("category"),
                        "price": metadata.get("price"),
                        "metadata": metadata
                    },
                    "similarity": hit["score"]
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"商品搜索失败: {e}")
            return []


class ChatService:
    """智能对话服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.vector_search = MilvusVectorSearchService(db)
        self.knowledge_graph = KnowledgeGraphService(db)
    
    async def create_session(self, user_id: str, session_type: str = "customer_service") -> ChatSessionModel:
        """创建聊天会话"""
        session = ChatSessionModel(
            user_id=user_id,
            session_type=session_type,
            context={"created_at": datetime.now().isoformat()}
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> ChatMessageModel:
        """添加聊天消息"""
        message = ChatMessageModel(
            session_id=session_id,
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message
    
    async def generate_response(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """生成智能回复"""
        try:
            # 1. 使用Milvus搜索相关文档
            similar_docs = await self.vector_search.search_similar_documents(
                query=user_message,
                document_types=["faq", "policy", "manual"],
                limit=3,
                use_milvus=True
            )
            
            # 2. 构建上下文
            context_docs = []
            for doc_info in similar_docs:
                context_docs.append({
                    "title": doc_info["document"]["title"],
                    "content": doc_info["document"]["content"][:500],  # 限制长度
                    "similarity": doc_info["similarity"]
                })
            
            # 3. 生成回复（这里使用简单的规则，实际可接入GPT等模型）
            response = await self._generate_rule_based_response(user_message, context_docs)
            
            # 4. 保存消息
            await self.add_message(session_id, "user", user_message)
            await self.add_message(session_id, "assistant", response["content"], response["metadata"])
            
            return response
            
        except Exception as e:
            return {
                "content": "抱歉，我遇到了一些问题，请稍后再试或联系人工客服。",
                "metadata": {"error": str(e)},
                "type": "error"
            }
    
    async def _generate_rule_based_response(
        self, 
        user_message: str, 
        context_docs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """基于规则生成回复"""
        user_message_lower = user_message.lower()
        
        # 订单相关问题
        if any(keyword in user_message_lower for keyword in ["订单", "order", "查询", "状态"]):
            if context_docs:
                return {
                    "content": f"关于订单问题，我找到了相关信息：\n\n{context_docs[0]['content']}\n\n如需查询具体订单，请提供订单号。",
                    "metadata": {"type": "order_inquiry", "context_used": True, "milvus_powered": True},
                    "type": "informational"
                }
            else:
                return {
                    "content": "请提供您的订单号，我来帮您查询订单状态。",
                    "metadata": {"type": "order_inquiry", "context_used": False},
                    "type": "request_info"
                }
        
        # 支付相关问题
        elif any(keyword in user_message_lower for keyword in ["支付", "payment", "付款", "退款"]):
            if context_docs:
                return {
                    "content": f"关于支付问题：\n\n{context_docs[0]['content']}\n\n如有具体支付问题，请提供更多详情。",
                    "metadata": {"type": "payment_inquiry", "context_used": True, "milvus_powered": True},
                    "type": "informational"
                }
            else:
                return {
                    "content": "我们支持多种支付方式，包括支付宝、微信支付等。请问您遇到了什么支付问题？",
                    "metadata": {"type": "payment_inquiry", "context_used": False},
                    "type": "informational"
                }
        
        # 发货相关问题
        elif any(keyword in user_message_lower for keyword in ["发货", "物流", "配送", "shipping"]):
            return {
                "content": "关于发货和物流，我们会在订单支付成功后24小时内安排发货。您可以通过订单号查询物流信息。",
                "metadata": {"type": "shipping_inquiry"},
                "type": "informational"
            }
        
        # 通用回复
        else:
            if context_docs:
                return {
                    "content": f"根据您的问题，我找到了相关信息：\n\n{context_docs[0]['content']}\n\n希望对您有帮助！",
                    "metadata": {"type": "general", "context_used": True, "milvus_powered": True},
                    "type": "informational"
                }
            else:
                return {
                    "content": "您好！我是智能客服助手，可以帮您解答订单、支付、发货等问题。请问有什么可以帮助您的吗？",
                    "metadata": {"type": "general", "context_used": False},
                    "type": "greeting"
                }


class AIAgentService:
    """AI Agent主服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.knowledge_graph = KnowledgeGraphService(db)
        self.vector_search = MilvusVectorSearchService(db)
        self.chat_service = ChatService(db)
    
    async def analyze_order_patterns(self, user_id: str) -> Dict[str, Any]:
        """分析用户订单模式"""
        try:
            # 从知识图谱中获取用户相关信息
            user_nodes = await self.knowledge_graph.find_related_nodes(
                node_id=user_id,
                relation_types=["belongs_to", "purchased"],
                max_depth=2
            )
            
            # 分析购买模式
            analysis = {
                "user_id": user_id,
                "total_orders": len([n for n in user_nodes if n["node"]["type"] == "order"]),
                "favorite_products": [],
                "spending_pattern": "regular",  # regular, high_value, frequent
                "recommendations": [],
                "powered_by": "milvus_knowledge_graph"
            }
            
            return analysis
            
        except Exception as e:
            return {"error": str(e)}
    
    async def risk_assessment(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """订单风险评估"""
        try:
            risk_score = 0.0
            risk_factors = []
            
            # 基于金额的风险评估
            amount = float(order_data.get("total_amount", 0))
            if amount > 10000:
                risk_score += 0.3
                risk_factors.append("高金额订单")
            
            # 基于用户历史的风险评估
            user_history = await self.knowledge_graph.find_related_nodes(
                node_id=order_data["user_id"],
                relation_types=["belongs_to"]
            )
            
            if len(user_history) == 0:
                risk_score += 0.4
                risk_factors.append("新用户")
            
            # 确定风险等级
            if risk_score < 0.3:
                risk_level = "low"
            elif risk_score < 0.6:
                risk_level = "medium"
            else:
                risk_level = "high"
            
            return {
                "order_id": order_data["id"],
                "risk_score": risk_score,
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "recommendations": self._get_risk_recommendations(risk_level),
                "powered_by": "milvus_ai_analysis"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _get_risk_recommendations(self, risk_level: str) -> List[str]:
        """获取风险处理建议"""
        recommendations = {
            "low": ["正常处理"],
            "medium": ["人工审核", "身份验证"],
            "high": ["暂停订单", "人工审核", "身份验证", "联系用户确认"]
        }
        return recommendations.get(risk_level, [])