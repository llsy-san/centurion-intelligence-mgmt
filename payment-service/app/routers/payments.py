"""
支付服务路由
定义支付相关的API接口
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Payment, PaymentCreate, PaymentStatus, BaseResponse
from ..utils import format_response
from ..database import get_db
from ..services import PaymentService

router = APIRouter()


@router.post("/", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """创建支付"""
    try:
        payment_service = PaymentService(db)
        payment = await payment_service.create_payment(payment_data)
        
        # 异步处理支付
        background_tasks.add_task(payment_service.process_payment, payment.id)
        
        return format_response(
            message="支付创建成功",
            data=payment.dict()
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="支付创建失败"
        )


@router.get("/{payment_id}", response_model=BaseResponse)
async def get_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """根据ID获取支付详情"""
    try:
        payment_service = PaymentService(db)
        payment = await payment_service.get_payment(payment_id)
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="支付记录不存在"
            )
        
        return format_response(
            message="获取支付成功",
            data=payment.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取支付失败"
        )


@router.get("/order/{order_id}", response_model=BaseResponse)
async def get_payment_by_order(
    order_id: str,
    db: AsyncSession = Depends(get_db)
):
    """根据订单ID获取支付详情"""
    try:
        payment_service = PaymentService(db)
        payment = await payment_service.get_payment_by_order(order_id)
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="支付记录不存在"
            )
        
        return format_response(
            message="获取支付成功",
            data=payment.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取支付失败"
        )


@router.post("/{payment_id}/process", response_model=BaseResponse)
async def process_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """手动处理支付"""
    try:
        payment_service = PaymentService(db)
        success = await payment_service.process_payment(payment_id)
        
        if success:
            return format_response(message="支付处理成功")
        else:
            return format_response(
                success=False,
                message="支付处理失败",
                error_code="PAYMENT_FAILED"
            )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="支付处理失败"
        )


@router.post("/{payment_id}/refund", response_model=BaseResponse)
async def refund_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db)
):
    """退款"""
    try:
        payment_service = PaymentService(db)
        success = await payment_service.refund_payment(payment_id)
        
        if success:
            return format_response(message="退款成功")
        else:
            return format_response(
                success=False,
                message="退款失败",
                error_code="REFUND_FAILED"
            )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="退款失败"
        )


@router.put("/{payment_id}/status", response_model=BaseResponse)
async def update_payment_status(
    payment_id: str,
    status: PaymentStatus,
    db: AsyncSession = Depends(get_db)
):
    """更新支付状态"""
    try:
        payment_service = PaymentService(db)
        success = await payment_service.update_payment_status(payment_id, status)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="支付记录不存在"
            )
        
        return format_response(message="支付状态更新成功")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="支付状态更新失败"
        )