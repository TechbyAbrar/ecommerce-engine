import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.auth.models import User
from app.common.responses import SuccessResponse
from app.core.dependencies import get_db
from app.payments.schemas import PaymentConfirm, PaymentInitiate, PaymentRead
from app.payments.service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post(
    "/orders/{order_id}/initiate",
    response_model=SuccessResponse[PaymentRead],
    status_code=status.HTTP_201_CREATED,
)
async def initiate_payment(order_id: uuid.UUID, data: PaymentInitiate, user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    return SuccessResponse(message="Payment initiated", data=await PaymentService(db).initiate(user, order_id, data))


@router.get("", response_model=SuccessResponse[list[PaymentRead]])
async def list_payments(user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    return SuccessResponse(data=await PaymentService(db).list_for_user(user))


@router.post("/{payment_id}/confirm", response_model=SuccessResponse[PaymentRead])
async def confirm_payment(payment_id: uuid.UUID, data: PaymentConfirm, user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    return SuccessResponse(message="Payment confirmed", data=await PaymentService(db).confirm(user, payment_id, data.payment_method_id))
