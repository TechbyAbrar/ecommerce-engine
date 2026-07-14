import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import PaginatedResponse, PaginationParams
from app.products.cache import product_cache
from app.products.exceptions import ProductNotFoundException, ProductSKUExistsException
from app.products.repository import ProductRepository
from app.products.schemas import ProductCreate, ProductRead, ProductUpdate


class ProductService:
    def __init__(self, db: AsyncSession):
        self.repository = ProductRepository(db)

    async def create(self, data: ProductCreate) -> ProductRead:
        if await self.repository.get_by_sku(data.sku):
            raise ProductSKUExistsException()
        try:
            product = ProductRead.model_validate(await self.repository.create(data))
            await product_cache.invalidate_lists()
            return product
        except IntegrityError as exc:
            await self.repository.db.rollback()
            raise ProductSKUExistsException() from exc

    async def get(self, product_id: uuid.UUID) -> ProductRead:
        key = f"products:detail:{product_id}"
        cached = await product_cache.get_json(key)
        if cached:
            return ProductRead.model_validate(cached)
        product = await self.repository.get(product_id)
        if not product:
            raise ProductNotFoundException()
        result = ProductRead.model_validate(product)
        await product_cache.set_json(key, result.model_dump(mode="json"))
        return result

    async def list(self, params: PaginationParams) -> PaginatedResponse[ProductRead]:
        version = await product_cache.list_version()
        key = f"products:list:{version}:{params.page}:{params.page_size}"
        cached = await product_cache.get_json(key)
        if cached:
            return PaginatedResponse[ProductRead].model_validate(cached)
        products, total = await self.repository.list_active(params)
        result = PaginatedResponse.create([ProductRead.model_validate(product) for product in products], total, params)
        await product_cache.set_json(key, result.model_dump(mode="json"))
        return result

    async def update(self, product_id: uuid.UUID, data: ProductUpdate) -> ProductRead:
        product = await self.repository.get(product_id)
        if not product:
            raise ProductNotFoundException()
        result = ProductRead.model_validate(await self.repository.update(product, data))
        await product_cache.delete(f"products:detail:{product_id}")
        await product_cache.invalidate_lists()
        return result

    async def delete(self, product_id: uuid.UUID) -> None:
        product = await self.repository.get(product_id)
        if not product:
            raise ProductNotFoundException()
        await self.repository.delete(product)
        await product_cache.delete(f"products:detail:{product_id}")
        await product_cache.invalidate_lists()
