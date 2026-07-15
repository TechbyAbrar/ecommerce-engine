import uuid
from collections.abc import Sequence

from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import PaginatedResponse, PaginationParams
from app.products.cache import product_cache
from app.products.exceptions import ProductNotFoundException, ProductSKUExistsException
from app.products.models import ProductImage
from app.products.repository import ProductRepository
from app.products.schemas import ProductCreate, ProductRead, ProductUpdate
from app.products.storage import ProductImageStorage, StoredProductImage


class ProductService:
    def __init__(self, db: AsyncSession):
        self.repository = ProductRepository(db)
        self.image_storage = ProductImageStorage()

    async def create(self, data: ProductCreate, images: Sequence[UploadFile] = ()) -> ProductRead:
        if await self.repository.get_by_sku(data.sku):
            raise ProductSKUExistsException()
        await self._validate_images(images)
        try:
            product = await self.repository.create(data)
        except IntegrityError as exc:
            await self._close_uploads(images)
            await self.repository.db.rollback()
            raise ProductSKUExistsException() from exc
        await self._add_images(product.id, images)
        product = await self.repository.get(product.id)
        assert product is not None
        result = ProductRead.model_validate(product)
        await product_cache.invalidate_lists()
        return result

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

    async def update(
        self, product_id: uuid.UUID, data: ProductUpdate, images: Sequence[UploadFile] = ()
    ) -> ProductRead:
        product = await self.repository.get(product_id)
        if not product:
            raise ProductNotFoundException()
        await self._validate_images(images)
        updated = await self.repository.update(product, data)
        await self._add_images(updated.id, images)
        result = ProductRead.model_validate(await self.repository.get(updated.id))
        await product_cache.delete(f"products:detail:{product_id}")
        await product_cache.invalidate_lists()
        return result

    async def delete(self, product_id: uuid.UUID) -> None:
        product = await self.repository.get(product_id)
        if not product:
            raise ProductNotFoundException()
        image_paths = [image.file_path for image in product.images]
        await self.repository.delete(product)
        for file_path in image_paths:
            self.image_storage.delete(file_path)
        await product_cache.delete(f"products:detail:{product_id}")
        await product_cache.invalidate_lists()

    async def clear_cache(self) -> bool:
        return await product_cache.clear()

    async def _add_images(self, product_id: uuid.UUID, uploads: Sequence[UploadFile]) -> None:
        if not uploads:
            return

        stored_images: list[StoredProductImage] = []
        try:
            for upload in uploads:
                stored_images.append(await self.image_storage.save(upload))
            max_order, has_primary = await self.repository.image_position(product_id)
            records = [
                ProductImage(
                    product_id=product_id,
                    file_path=image.file_path,
                    original_filename=image.original_filename,
                    content_type=image.content_type,
                    file_size=image.file_size,
                    is_primary=not has_primary and index == 0,
                    display_order=max_order + index + 1,
                )
                for index, image in enumerate(stored_images)
            ]
            await self.repository.create_images(records)
        except Exception:
            await self.repository.db.rollback()
            for image in stored_images:
                self.image_storage.delete(image.file_path)
            raise

    async def _validate_images(self, uploads: Sequence[UploadFile]) -> None:
        try:
            for upload in uploads:
                await self.image_storage.validate(upload)
        except Exception:
            await self._close_uploads(uploads)
            raise

    async def _close_uploads(self, uploads: Sequence[UploadFile]) -> None:
        for upload in uploads:
            await upload.close()
