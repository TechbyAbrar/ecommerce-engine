import uuid

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import PaginatedResponse, PaginationParams, pagination_params
from app.common.responses import SuccessResponse
from app.core.dependencies import get_db
from app.products.dependencies import product_create_data, product_update_data, require_admin
from app.products.schemas import ProductCreate, ProductRead, ProductUpdate
from app.products.service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=SuccessResponse[PaginatedResponse[ProductRead]])
async def list_products(params: PaginationParams = Depends(pagination_params), db: AsyncSession = Depends(get_db)):
    return SuccessResponse(data=await ProductService(db).list(params))


@router.get("/{product_id}", response_model=SuccessResponse[ProductRead])
async def get_product(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return SuccessResponse(data=await ProductService(db).get(product_id))


@router.post(
    "",
    response_model=SuccessResponse[ProductRead],
    status_code=status.HTTP_201_CREATED,
    tags=["Admin Products"],
)
async def create_product(
    data: ProductCreate = Depends(product_create_data),
    images: list[UploadFile] | None = File(default=None),
    _: object = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return SuccessResponse(message="Product created", data=await ProductService(db).create(data, images or []))


@router.patch("/{product_id}", response_model=SuccessResponse[ProductRead], tags=["Admin Products"])
async def update_product(
    product_id: uuid.UUID,
    data: ProductUpdate = Depends(product_update_data),
    images: list[UploadFile] | None = File(default=None),
    _: object = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return SuccessResponse(message="Product updated", data=await ProductService(db).update(product_id, data, images or []))


@router.delete("/{product_id}", response_model=SuccessResponse[None], tags=["Admin Products"])
async def delete_product(product_id: uuid.UUID, _: object = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    await ProductService(db).delete(product_id)
    return SuccessResponse(message="Product deleted", data=None)
