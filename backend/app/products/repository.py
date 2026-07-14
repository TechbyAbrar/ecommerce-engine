import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import PaginationParams
from app.products.models import Product, ProductStatus
from app.products.schemas import ProductCreate, ProductUpdate


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, product_id: uuid.UUID, *, lock: bool = False) -> Product | None:
        statement = select(Product).where(Product.id == product_id)
        if lock:
            statement = statement.with_for_update()
        return await self.db.scalar(statement)

    async def get_by_sku(self, sku: str) -> Product | None:
        return await self.db.scalar(select(Product).where(Product.sku == sku))

    async def list_active(self, params: PaginationParams) -> tuple[list[Product], int]:
        where = Product.status == ProductStatus.ACTIVE
        total = await self.db.scalar(select(func.count()).select_from(Product).where(where)) or 0
        result = await self.db.scalars(
            select(Product).where(where).order_by(Product.created_at.desc()).offset(params.offset).limit(params.page_size)
        )
        return list(result), total

    async def create(self, data: ProductCreate) -> Product:
        product = Product(**data.model_dump())
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def update(self, product: Product, data: ProductUpdate) -> Product:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(product, field, value)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def delete(self, product: Product) -> None:
        await self.db.delete(product)
        await self.db.commit()
