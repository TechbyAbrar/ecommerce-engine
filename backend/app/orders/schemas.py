import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.orders.models import OrderStatus


class OrderItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(ge=1, le=10_000)


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderItemRead(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    quantity: int
    price: Decimal
    subtotal: Decimal

    model_config = {"from_attributes": True}


class OrderRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    total_amount: Decimal
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemRead]

    model_config = {"from_attributes": True}
