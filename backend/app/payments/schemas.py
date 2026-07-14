import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.payments.models import PaymentProvider, PaymentStatus


class PaymentInitiate(BaseModel):
    provider: PaymentProvider
    return_url: str | None = Field(default=None, max_length=2048)


class PaymentConfirm(BaseModel):
    payment_method_id: str | None = Field(default=None, min_length=1, max_length=255)


class PaymentRead(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    provider: PaymentProvider
    transaction_id: str
    status: PaymentStatus
    raw_response: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WebhookPayload(BaseModel):
    transaction_id: str
    status: PaymentStatus
    raw_response: dict[str, Any] = Field(default_factory=dict)


class BKashCallback(BaseModel):
    paymentID: str = Field(min_length=1, max_length=255)
