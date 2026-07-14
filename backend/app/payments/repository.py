import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.payments.models import Payment, PaymentProvider, PaymentStatus


class PaymentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, payment_id: uuid.UUID, *, lock: bool = False) -> Payment | None:
        statement = select(Payment).where(Payment.id == payment_id)
        if lock:
            statement = statement.with_for_update()
        return await self.db.scalar(statement)

    async def get_by_transaction(self, transaction_id: str, *, lock: bool = False) -> Payment | None:
        statement = select(Payment).where(Payment.transaction_id == transaction_id)
        if lock:
            statement = statement.with_for_update()
        return await self.db.scalar(statement)

    async def list_for_order_ids(self, order_ids: list[uuid.UUID]) -> list[Payment]:
        if not order_ids:
            return []
        result = await self.db.scalars(
            select(Payment).where(Payment.order_id.in_(order_ids)).order_by(Payment.created_at.desc())
        )
        return list(result)

    async def create(self, order_id: uuid.UUID, provider: PaymentProvider, transaction_id: str, raw_response: dict[str, Any]) -> Payment:
        payment = Payment(order_id=order_id, provider=provider, transaction_id=transaction_id, raw_response=raw_response)
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)
        return payment

    async def set_status(self, payment: Payment, status: PaymentStatus, raw_response: dict[str, Any]) -> None:
        payment.status = status
        payment.raw_response = raw_response
