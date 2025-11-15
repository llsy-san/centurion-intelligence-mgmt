"""
Milvus向量数据库服务
提供高性能向量存储和搜索功能
"""
from pymilvus import (
    connections, Collection, CollectionSchema, FieldSchema, DataType,
    utility, Index
)
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import json
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import os

logger = logging.getLogger(__name__)


class MilvusService:
    """Milvus向量数据库服务"""
    
    def __init__(self):
        self.host = os.getenv("MILVUS_HOST", "localhost")
        self.port = int(os.getenv("MILVUS_PORT", "19530"))
        self.connection_alias = "default"
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # 集合配置
        self.collections_config = {
            "documents": {
                "description": "文档向量集合",
                "dimension": 1536,
                "fields": [
                    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                    FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=100),
                    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),
                    FieldSchema(name="metadata", dtype=DataType.JSON)
                ]
            },
            "products": {
                "description": "商品向量集合",
                "dimension": 1536,
                "fields": [
                    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                    FieldSchema(name="product_id", dtype=DataType.VARCHAR, max_length=100),
                    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),
                    FieldSchema(name="metadata", dtype=DataType.JSON)
                ]
            },
            "users": {
                "description": "用户行为向量集合",
                "dimension": 512,
                "fields": [
                    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                    FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=100),
                    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=512),
                    FieldSchema(name="metadata", dtype=DataType.JSON)
                ]
            }
        }
    
    async def connect(self):
        """连接到Milvus"""
        try:
            # 在线程池中执行连接操作
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._connect_sync
            )
            logger.info(f"✅ 成功连接到Milvus: {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"❌ 连接Milvus失败: {e}")
            raise
    
    def _connect_sync(self):
        """同步连接方法"""
        connections.connect(
            alias=self.connection_alias,
            host=self.host,
            port=self.port
        )
    
    async def initialize_collections(self):
        """初始化所有集合"""
        try:
            for collection_name, config in self.collections_config.items():
                await self._create_collection_if_not_exists(collection_name, config)
            logger.info("✅ 所有Milvus集合初始化完成")
        except Exception as e:
            logger.error(f"❌ 初始化Milvus集合失败: {e}")
            raise
    
    async def _create_collection_if_not_exists(self, collection_name: str, config: Dict[str, Any]):
        """创建集合（如果不存在）"""
        await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self._create_collection_sync,
            collection_name,
            config
        )
    
    def _create_collection_sync(self, collection_name: str, config: Dict[str, Any]):
        """同步创建集合"""
        # 检查集合是否存在
        if utility.has_collection(collection_name):
            logger.info(f"📋 集合 '{collection_name}' 已存在")
            return
        
        # 创建集合schema
        schema = CollectionSchema(
            fields=config["fields"],
            description=config["description"]
        )
        
        # 创建集合
        collection = Collection(
            name=collection_name,
            schema=schema,
            using=self.connection_alias
        )
        
        # 创建索引
        self._create_index(collection, config["dimension"])
        
        logger.info(f"✅ 创建集合 '{collection_name}' 成功")
    
    def _create_index(self, collection: Collection, dimension: int):
        """为集合创建向量索引"""
        # 选择索引类型和参数
        if dimension <= 512:
            # 小维度使用HNSW索引
            index_params = {
                "metric_type": "L2",
                "index_type": "HNSW",
                "params": {"M": 16, "efConstruction": 200}
            }
        else:
            # 大维度使用IVF_FLAT索引
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
        
        # 创建索引
        collection.create_index(
            field_name="embedding",
            index_params=index_params
        )
        
        # 加载集合到内存
        collection.load()
    
    async def insert_vectors(
        self,
        collection_name: str,
        entity_ids: List[str],
        embeddings: List[List[float]],
        metadata_list: List[Dict[str, Any]]
    ) -> List[int]:
        """插入向量数据"""
        return await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self._insert_vectors_sync,
            collection_name,
            entity_ids,
            embeddings,
            metadata_list
        )
    
    def _insert_vectors_sync(
        self,
        collection_name: str,
        entity_ids: List[str],
        embeddings: List[List[float]],
        metadata_list: List[Dict[str, Any]]
    ) -> List[int]:
        """同步插入向量数据"""
        collection = Collection(collection_name)
        
        # 准备数据
        if collection_name == "documents":
            entities = [entity_ids, embeddings, metadata_list]
        elif collection_name == "products":
            entities = [entity_ids, embeddings, metadata_list]
        elif collection_name == "users":
            entities = [entity_ids, embeddings, metadata_list]
        else:
            raise ValueError(f"未知的集合名称: {collection_name}")
        
        # 插入数据
        insert_result = collection.insert(entities)
        collection.flush()
        
        return insert_result.primary_keys
    
    async def search_vectors(
        self,
        collection_name: str,
        query_vectors: List[List[float]],
        top_k: int = 10,
        search_params: Optional[Dict[str, Any]] = None,
        filter_expr: Optional[str] = None
    ) -> List[List[Dict[str, Any]]]:
        """搜索相似向量"""
        return await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self._search_vectors_sync,
            collection_name,
            query_vectors,
            top_k,
            search_params,
            filter_expr
        )
    
    def _search_vectors_sync(
        self,
        collection_name: str,
        query_vectors: List[List[float]],
        top_k: int = 10,
        search_params: Optional[Dict[str, Any]] = None,
        filter_expr: Optional[str] = None
    ) -> List[List[Dict[str, Any]]]:
        """同步搜索相似向量"""
        collection = Collection(collection_name)
        
        # 默认搜索参数
        if search_params is None:
            search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        
        # 执行搜索
        search_results = collection.search(
            data=query_vectors,
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=filter_expr,
            output_fields=["*"]
        )
        
        # 格式化结果
        formatted_results = []
        for hits in search_results:
            hit_list = []
            for hit in hits:
                hit_dict = {
                    "id": hit.id,
                    "distance": hit.distance,
                    "score": 1.0 / (1.0 + hit.distance),  # 转换为相似度分数
                    "entity": hit.entity
                }
                hit_list.append(hit_dict)
            formatted_results.append(hit_list)
        
        return formatted_results
    
    async def delete_vectors(
        self,
        collection_name: str,
        filter_expr: str
    ) -> int:
        """删除向量数据"""
        return await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self._delete_vectors_sync,
            collection_name,
            filter_expr
        )
    
    def _delete_vectors_sync(self, collection_name: str, filter_expr: str) -> int:
        """同步删除向量数据"""
        collection = Collection(collection_name)
        delete_result = collection.delete(filter_expr)
        collection.flush()
        return delete_result.delete_count
    
    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """获取集合统计信息"""
        return await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self._get_collection_stats_sync,
            collection_name
        )
    
    def _get_collection_stats_sync(self, collection_name: str) -> Dict[str, Any]:
        """同步获取集合统计信息"""
        collection = Collection(collection_name)
        stats = collection.get_stats()
        
        return {
            "name": collection_name,
            "num_entities": stats["row_count"],
            "num_segments": len(stats.get("segments", [])),
            "schema": {
                "fields": [
                    {
                        "name": field.name,
                        "type": str(field.dtype),
                        "description": field.description
                    }
                    for field in collection.schema.fields
                ]
            }
        }
    
    async def create_hybrid_search(
        self,
        collection_name: str,
        query_vector: List[float],
        metadata_filters: Dict[str, Any],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """混合搜索：向量相似度 + 元数据过滤"""
        # 构建过滤表达式
        filter_expressions = []
        for key, value in metadata_filters.items():
            if isinstance(value, str):
                filter_expressions.append(f'metadata["{key}"] == "{value}"')
            elif isinstance(value, (int, float)):
                filter_expressions.append(f'metadata["{key}"] == {value}')
            elif isinstance(value, list):
                # 支持IN查询
                value_str = ", ".join([f'"{v}"' if isinstance(v, str) else str(v) for v in value])
                filter_expressions.append(f'metadata["{key}"] in [{value_str}]')
        
        filter_expr = " and ".join(filter_expressions) if filter_expressions else None
        
        # 执行搜索
        results = await self.search_vectors(
            collection_name=collection_name,
            query_vectors=[query_vector],
            top_k=top_k,
            filter_expr=filter_expr
        )
        
        return results[0] if results else []
    
    async def batch_insert_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[int]:
        """批量插入文档向量"""
        entity_ids = [doc["document_id"] for doc in documents]
        embeddings = [doc["embedding"] for doc in documents]
        metadata_list = [doc["metadata"] for doc in documents]
        
        return await self.insert_vectors(
            collection_name="documents",
            entity_ids=entity_ids,
            embeddings=embeddings,
            metadata_list=metadata_list
        )
    
    async def batch_insert_products(
        self,
        products: List[Dict[str, Any]]
    ) -> List[int]:
        """批量插入商品向量"""
        entity_ids = [prod["product_id"] for prod in products]
        embeddings = [prod["embedding"] for prod in products]
        metadata_list = [prod["metadata"] for prod in products]
        
        return await self.insert_vectors(
            collection_name="products",
            entity_ids=entity_ids,
            embeddings=embeddings,
            metadata_list=metadata_list
        )
    
    async def search_similar_documents(
        self,
        query_embedding: List[float],
        document_types: List[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """搜索相似文档"""
        metadata_filters = {}
        if document_types:
            metadata_filters["document_type"] = document_types
        
        return await self.create_hybrid_search(
            collection_name="documents",
            query_vector=query_embedding,
            metadata_filters=metadata_filters,
            top_k=top_k
        )
    
    async def search_similar_products(
        self,
        query_embedding: List[float],
        categories: List[str] = None,
        price_range: Tuple[float, float] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """搜索相似商品"""
        metadata_filters = {}
        if categories:
            metadata_filters["category"] = categories
        
        # 价格范围过滤需要特殊处理
        results = await self.search_vectors(
            collection_name="products",
            query_vectors=[query_embedding],
            top_k=top_k * 2  # 获取更多结果用于价格过滤
        )
        
        # 后处理价格过滤
        if price_range and results:
            filtered_results = []
            min_price, max_price = price_range
            
            for hit in results[0]:
                metadata = hit.get("entity", {}).get("metadata", {})
                price = metadata.get("price", 0)
                if min_price <= price <= max_price:
                    filtered_results.append(hit)
                    if len(filtered_results) >= top_k:
                        break
            
            return filtered_results
        
        return results[0] if results else []
    
    async def disconnect(self):
        """断开连接"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                connections.disconnect,
                self.connection_alias
            )
            logger.info("🔌 Milvus连接已断开")
        except Exception as e:
            logger.error(f"❌ 断开Milvus连接失败: {e}")


# 全局Milvus服务实例
milvus_service = MilvusService()