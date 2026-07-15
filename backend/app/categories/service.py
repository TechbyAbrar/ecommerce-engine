"""Category hierarchy business rules and cached tree access."""
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.categories import cache
from app.categories.dfs import build_category_tree
from app.categories.models import Category
from app.categories.repository import CategoryRepository
from app.categories.schemas import CategoryCreate, CategoryRead, CategoryTreeRead, CategoryUpdate
from app.core.exceptions import ConflictException, NotFoundException


class CategoryNotFoundException(NotFoundException):
    error_code = "CATEGORY_NOT_FOUND"


class CategoryConflictException(ConflictException):
    error_code = "CATEGORY_CONFLICT"


class CategoryService:
    def __init__(self, db: AsyncSession):
        self.repository = CategoryRepository(db)

    async def tree(self) -> list[CategoryTreeRead]:
        cached = await cache.get_tree()
        if cached is not None:
            return [CategoryTreeRead.model_validate(item) for item in cached]
        tree = build_category_tree(await self.repository.list_active())
        result = [CategoryTreeRead.model_validate(item) for item in tree]
        await cache.set_tree([item.model_dump(mode="json") for item in result])
        return result

    async def create(self, data: CategoryCreate) -> CategoryRead:
        await self._validate_parent(data.parent_id)
        if await self.repository.get_by_slug(data.slug):
            raise CategoryConflictException("A category with this slug already exists")
        try:
            category = await self.repository.create(data)
        except IntegrityError as exc:
            await self.repository.db.rollback()
            raise CategoryConflictException("A category with this slug already exists") from exc
        await cache.invalidate_tree()
        return CategoryRead.model_validate(category)

    async def update(self, category_id: uuid.UUID, data: CategoryUpdate) -> CategoryRead:
        category = await self._get(category_id)
        if data.slug and data.slug != category.slug:
            existing = await self.repository.get_by_slug(data.slug)
            if existing and existing.id != category.id:
                raise CategoryConflictException("A category with this slug already exists")
        if "parent_id" in data.model_fields_set:
            await self._validate_parent(data.parent_id, category)
        try:
            updated = await self.repository.update(category, data)
        except IntegrityError as exc:
            await self.repository.db.rollback()
            raise CategoryConflictException("Category update violates a hierarchy constraint") from exc
        await cache.invalidate_tree()
        return CategoryRead.model_validate(updated)

    async def delete(self, category_id: uuid.UUID) -> None:
        category = await self._get(category_id)
        if await self.repository.has_children(category.id):
            raise CategoryConflictException("Delete or reassign child categories first")
        await self.repository.delete(category)
        await cache.invalidate_tree()

    async def _get(self, category_id: uuid.UUID) -> Category:
        category = await self.repository.get(category_id)
        if not category:
            raise CategoryNotFoundException()
        return category

    async def _validate_parent(self, parent_id: uuid.UUID | None, category: Category | None = None) -> None:
        if parent_id is None:
            return
        if category and parent_id == category.id:
            raise CategoryConflictException("A category cannot be its own parent")
        parent = await self.repository.get(parent_id)
        if not parent or not parent.is_active:
            raise CategoryNotFoundException("Parent category was not found or is inactive")
        if category:
            cursor = parent
            while cursor.parent_id is not None:
                if cursor.parent_id == category.id:
                    raise CategoryConflictException("Category hierarchy cannot contain a cycle")
                cursor = await self.repository.get(cursor.parent_id)
                if cursor is None:
                    break
