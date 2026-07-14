import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.orders.models import Order, OrderStatus


class OrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, order_id: uuid.UUID, user_id: uuid.UUID | None = None, *, lock: bool = False) -> Order | None:
        statement = select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
        if user_id is not None:
            statement = statement.where(Order.user_id == user_id)
        if lock:
            statement = statement.with_for_update()
        return await self.db.scalar(statement)

    async def list_for_user(self, user_id: uuid.UUID) -> list[Order]:
        result = await self.db.scalars(
            select(Order).options(selectinload(Order.items)).where(Order.user_id == user_id).order_by(Order.created_at.desc())
        )
        return list(result)

    async def list_ids_for_user(self, user_id: uuid.UUID) -> list[uuid.UUID]:
        """Fetch only order IDs for payment history; avoid loading order items."""
        result = await self.db.scalars(select(Order.id).where(Order.user_id == user_id))
        return list(result)

    async def create(self, order: Order) -> Order:
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order, ["items"])
        return order

    async def mark_paid(self, order: Order) -> None:
        order.status = OrderStatus.PAID
