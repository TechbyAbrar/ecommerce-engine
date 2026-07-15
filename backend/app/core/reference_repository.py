from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.reference_models import ReferenceData


class ReferenceDataRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert(self, key: str, value: dict[str, Any]) -> None:
        record = await self.db.get(ReferenceData, key)
        if record:
            record.value = value
        else:
            self.db.add(ReferenceData(key=key, value=value))
        await self.db.commit()
