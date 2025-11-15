"""
向量搜索相关路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from pydantic import BaseModel

from ..database import get_db
from ..services import VectorSearchService

router = APIRouter()


class DocumentAddRequest(BaseModel):
    """添加文档请求"""
    document_type: str
    title: str
    content: str
    metadata: Dict[str, Any] = {}
    tags: List[str] = []


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str
    document_types: List[str] = None
    limit: int = 5
    similarity_threshold: float = 0.7


@router.post("/documents/", summary="添加文档到向量数据库")
async def add_document(
    request: DocumentAddRequest,
    db: AsyncSession = Depends(get_db)
):
    """添加文档到向量数据库"""
    service = VectorSearchService(db)
    
    try:
        document = await service.add_document(
            document_type=request.document_type,
            title=request.title,
            content=request.content,
            metadata=request.metadata,
            tags=request.tags
        )
        
        return {
            "status": "success",
            "document": {
                "id": str(document.id),
                "type": document.document_type,
                "title": document.title,
                "metadata": document.metadata,
                "tags": document.tags
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/", summary="向量相似度搜索")
async def search_documents(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """搜索相似文档"""
    service = VectorSearchService(db)
    
    try:
        results = await service.search_similar_documents(
            query=request.query,
            document_types=request.document_types,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold
        )
        
        return {
            "status": "success",
            "query": request.query,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/batch", summary="批量添加文档")
async def add_documents_batch(
    documents: List[DocumentAddRequest],
    db: AsyncSession = Depends(get_db)
):
    """批量添加文档"""
    service = VectorSearchService(db)
    results = []
    
    for doc_request in documents:
        try:
            document = await service.add_document(
                document_type=doc_request.document_type,
                title=doc_request.title,
                content=doc_request.content,
                metadata=doc_request.metadata,
                tags=doc_request.tags
            )
            
            results.append({
                "status": "success",
                "document_id": str(document.id),
                "title": document.title
            })
        except Exception as e:
            results.append({
                "status": "error",
                "title": doc_request.title,
                "error": str(e)
            })
    
    return {
        "status": "completed",
        "total": len(documents),
        "results": results
    }