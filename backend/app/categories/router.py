"""HTTP endpoints for the category hierarchy."""
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_roles
from app.common.enums import UserRole
from app.common.responses import SuccessResponse
from app.categories.schemas import CategoryCreate, CategoryRead, CategoryTreeRead, CategoryUpdate
from app.categories.service import CategoryService
from app.core.dependencies import get_db

router = APIRouter(prefix="/categories", tags=["Categories"])
require_category_admin = require_roles(UserRole.ADMIN, UserRole.SUPERUSER)


@router.get("", response_model=SuccessResponse[list[CategoryTreeRead]])
async def list_categories(db: AsyncSession = Depends(get_db)):
    return SuccessResponse(data=await CategoryService(db).tree())


@router.post("", response_model=SuccessResponse[CategoryRead], status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    _: object = Depends(require_category_admin),
    db: AsyncSession = Depends(get_db),
):
    return SuccessResponse(message="Category created", data=await CategoryService(db).create(data))


@router.patch("/{category_id}", response_model=SuccessResponse[CategoryRead])
async def update_category(
    category_id: uuid.UUID,
    data: CategoryUpdate,
    _: object = Depends(require_category_admin),
    db: AsyncSession = Depends(get_db),
):
    return SuccessResponse(message="Category updated", data=await CategoryService(db).update(category_id, data))


@router.delete("/{category_id}", response_model=SuccessResponse[None])
async def delete_category(
    category_id: uuid.UUID,
    _: object = Depends(require_category_admin),
    db: AsyncSession = Depends(get_db),
):
    await CategoryService(db).delete(category_id)
    return SuccessResponse(message="Category deleted", data=None)
