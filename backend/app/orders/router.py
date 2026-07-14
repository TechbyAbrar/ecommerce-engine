import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.auth.models import User
from app.common.responses import SuccessResponse
from app.core.dependencies import get_db
from app.orders.schemas import OrderCreate, OrderRead
from app.orders.service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=SuccessResponse[OrderRead], status_code=status.HTTP_201_CREATED)
async def create_order(data: OrderCreate, user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    return SuccessResponse(message="Order created", data=await OrderService(db).create(user, data))


@router.get("", response_model=SuccessResponse[list[OrderRead]])
async def list_orders(user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    return SuccessResponse(data=await OrderService(db).list_for_user(user))


@router.get("/{order_id}", response_model=SuccessResponse[OrderRead])
async def get_order(order_id: uuid.UUID, user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    return SuccessResponse(data=await OrderService(db).get(user, order_id))
