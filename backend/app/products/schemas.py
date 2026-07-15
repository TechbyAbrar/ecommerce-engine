import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.products.models import ProductStatus


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    sku: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=4000)
    category_id: uuid.UUID | None = None
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    stock: int = Field(ge=0)
    status: ProductStatus = ProductStatus.ACTIVE

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, value: str) -> str:
        return value.strip().upper()


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    category_id: uuid.UUID | None = None
    price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    stock: int | None = Field(default=None, ge=0)
    status: ProductStatus | None = None


class ProductImageRead(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    file_path: str
    original_filename: str
    content_type: str
    file_size: int
    is_primary: bool
    display_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductRead(BaseModel):
    id: uuid.UUID
    name: str
    sku: str
    description: str | None
    category_id: uuid.UUID | None
    price: Decimal
    stock: int
    status: ProductStatus
    created_at: datetime
    updated_at: datetime
    images: list[ProductImageRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}
