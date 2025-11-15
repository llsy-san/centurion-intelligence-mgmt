"""
知识图谱相关路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from pydantic import BaseModel

from ..database import get_db
from ..services import KnowledgeGraphService

router = APIRouter()


class NodeCreateRequest(BaseModel):
    """创建节点请求"""
    node_type: str
    entity_id: str
    name: str
    properties: Dict[str, Any] = {}


class RelationCreateRequest(BaseModel):
    """创建关系请求"""
    source_node_id: str
    target_node_id: str
    relation_type: str
    properties: Dict[str, Any] = {}
    weight: float = 1.0


@router.post("/nodes/", summary="创建知识图谱节点")
async def create_node(
    request: NodeCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """创建知识图谱节点"""
    service = KnowledgeGraphService(db)
    
    try:
        node = await service.create_node(
            node_type=request.node_type,
            entity_id=request.entity_id,
            name=request.name,
            properties=request.properties
        )
        
        return {
            "status": "success",
            "node": {
                "id": str(node.id),
                "type": node.node_type,
                "entity_id": node.entity_id,
                "name": node.name,
                "properties": node.properties
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/relations/", summary="创建知识图谱关系")
async def create_relation(
    request: RelationCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """创建知识图谱关系"""
    service = KnowledgeGraphService(db)
    
    try:
        relation = await service.create_relation(
            source_node_id=request.source_node_id,
            target_node_id=request.target_node_id,
            relation_type=request.relation_type,
            properties=request.properties,
            weight=request.weight
        )
        
        return {
            "status": "success",
            "relation": {
                "id": str(relation.id),
                "source_node_id": str(relation.source_node_id),
                "target_node_id": str(relation.target_node_id),
                "relation_type": relation.relation_type,
                "properties": relation.properties,
                "weight": relation.weight
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes/{node_id}/related", summary="获取相关节点")
async def get_related_nodes(
    node_id: str,
    relation_types: str = None,
    max_depth: int = 2,
    db: AsyncSession = Depends(get_db)
):
    """获取节点的相关节点"""
    service = KnowledgeGraphService(db)
    
    try:
        relation_type_list = None
        if relation_types:
            relation_type_list = relation_types.split(",")
        
        related_nodes = await service.find_related_nodes(
            node_id=node_id,
            relation_types=relation_type_list,
            max_depth=max_depth
        )
        
        return {
            "status": "success",
            "node_id": node_id,
            "related_nodes": related_nodes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/build/order", summary="构建订单知识图谱")
async def build_order_knowledge_graph(
    order_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """构建订单相关的知识图谱"""
    service = KnowledgeGraphService(db)
    
    try:
        result = await service.build_order_knowledge_graph(order_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))