"""Database access for categories."""
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.categories.models import Category
from app.categories.schemas import CategoryCreate, CategoryUpdate


class CategoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, category_id: uuid.UUID) -> Category | None:
        return await self.db.scalar(select(Category).where(Category.id == category_id))

    async def get_by_slug(self, slug: str) -> Category | None:
        return await self.db.scalar(select(Category).where(Category.slug == slug))

    async def list_active(self) -> list[Category]:
        result = await self.db.scalars(
            select(Category).options(selectinload(Category.children)).where(Category.is_active.is_(True))
        )
        return list(result)

    async def has_children(self, category_id: uuid.UUID) -> bool:
        return bool(await self.db.scalar(select(func.count()).select_from(Category).where(Category.parent_id == category_id)))

    async def create(self, data: CategoryCreate) -> Category:
        category = Category(**data.model_dump())
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def update(self, category: Category, data: CategoryUpdate) -> Category:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(category, field, value)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def delete(self, category: Category) -> None:
        await self.db.delete(category)
        await self.db.commit()
