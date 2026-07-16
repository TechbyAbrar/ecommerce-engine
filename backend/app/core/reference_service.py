"""Idempotent reference-data provisioning for CLI operations."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import UserRole
from app.core.reference_repository import ReferenceDataRepository
from app.orders.models import OrderStatus
from app.payments.models import PaymentProvider


class ReferenceDataService:
    def __init__(self, db: AsyncSession):
        self.repository = ReferenceDataRepository(db)

    async def seed(self) -> int:
        records = {
            "roles": {"values": [role.value for role in UserRole]},
            "permissions": {"values": []},
            "categories": {"values": []},
            "order_statuses": {"values": [status.value for status in OrderStatus]},
            "payment_methods": {"values": [provider.value for provider in PaymentProvider]},
            "shipping_methods": {"values": []},
            "system_settings": {"currency": "USD", "locale": "en"},
        }
        for key, value in records.items():
            await self.repository.upsert(key, value)
        return len(records)
