import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.utils import utc_now
from app.core.database import Base

if TYPE_CHECKING:
    from app.categories.models import Category


class ProductStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_status_created_at", "status", "created_at"),
        Index("ix_products_category_status_created_at", "category_id", "status", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(4000))
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=True
    )
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[ProductStatus] = mapped_column(
        Enum(ProductStatus, name="product_status"), nullable=False, default=ProductStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    category: Mapped["Category | None"] = relationship("Category", back_populates="products")
    images: Mapped[list["ProductImage"]] = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ProductImage.display_order",
    )


class ProductImage(Base):
    __tablename__ = "product_images"
    __table_args__ = (
        Index("ix_product_images_product_display_order", "product_id", "display_order"),
        Index(
            "uq_product_images_primary",
            "product_id",
            unique=True,
            postgresql_where=text("is_primary IS true"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    product: Mapped[Product] = relationship("Product", back_populates="images")


# Register the other side for mapper configuration when this module is imported alone.
from app.categories.models import Category  # noqa: E402, F401
