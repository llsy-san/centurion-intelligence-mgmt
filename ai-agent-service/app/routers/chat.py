"""
智能对话相关路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from pydantic import BaseModel

from ..database import get_db
from ..services import ChatService, AIAgentService

router = APIRouter()


class ChatSessionRequest(BaseModel):
    """创建聊天会话请求"""
    user_id: str
    session_type: str = "customer_service"


class ChatMessageRequest(BaseModel):
    """发送消息请求"""
    session_id: str
    message: str


class OrderAnalysisRequest(BaseModel):
    """订单分析请求"""
    user_id: str


class RiskAssessmentRequest(BaseModel):
    """风险评估请求"""
    order_data: Dict[str, Any]


@router.post("/sessions/", summary="创建聊天会话")
async def create_chat_session(
    request: ChatSessionRequest,
    db: AsyncSession = Depends(get_db)
):
    """创建新的聊天会话"""
    service = ChatService(db)
    
    try:
        session = await service.create_session(
            user_id=request.user_id,
            session_type=request.session_type
        )
        
        return {
            "status": "success",
            "session": {
                "id": str(session.id),
                "user_id": session.user_id,
                "session_type": session.session_type,
                "status": session.status,
                "created_at": session.created_at.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message/", summary="发送聊天消息")
async def send_message(
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    """发送消息并获取AI回复"""
    service = ChatService(db)
    
    try:
        response = await service.generate_response(
            session_id=request.session_id,
            user_message=request.message
        )
        
        return {
            "status": "success",
            "session_id": request.session_id,
            "user_message": request.message,
            "ai_response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/order-patterns", summary="分析用户订单模式")
async def analyze_order_patterns(
    request: OrderAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """分析用户的订单模式"""
    service = AIAgentService(db)
    
    try:
        analysis = await service.analyze_order_patterns(request.user_id)
        return {
            "status": "success",
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assess/risk", summary="订单风险评估")
async def assess_order_risk(
    request: RiskAssessmentRequest,
    db: AsyncSession = Depends(get_db)
):
    """评估订单风险"""
    service = AIAgentService(db)
    
    try:
        assessment = await service.risk_assessment(request.order_data)
        return {
            "status": "success",
            "assessment": assessment
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/history", summary="获取聊天历史")
async def get_chat_history(
    session_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """获取聊天会话历史"""
    from sqlalchemy import select
    from ..database import ChatMessageModel
    
    try:
        query = select(ChatMessageModel).where(
            ChatMessageModel.session_id == session_id
        ).order_by(ChatMessageModel.created_at.desc()).limit(limit)
        
        result = await db.execute(query)
        messages = result.scalars().all()
        
        history = []
        for msg in reversed(messages):  # 按时间正序返回
            history.append({
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "metadata": msg.metadata,
                "created_at": msg.created_at.isoformat()
            })
        
        return {
            "status": "success",
            "session_id": session_id,
            "messages": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))