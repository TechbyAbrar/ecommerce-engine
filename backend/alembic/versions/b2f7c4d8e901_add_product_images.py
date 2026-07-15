"""Add product images.

Revision ID: b2f7c4d8e901
Revises: a74a55d59845
Create Date: 2026-07-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2f7c4d8e901"
down_revision: Union[str, Sequence[str], None] = "a74a55d59845"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "product_images",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_product_images_product_display_order",
        "product_images",
        ["product_id", "display_order"],
        unique=False,
    )
    op.create_index(
        "uq_product_images_primary",
        "product_images",
        ["product_id"],
        unique=True,
        postgresql_where=sa.text("is_primary IS true"),
    )


def downgrade() -> None:
    op.drop_index("uq_product_images_primary", table_name="product_images", postgresql_where=sa.text("is_primary IS true"))
    op.drop_index("ix_product_images_product_display_order", table_name="product_images")
    op.drop_table("product_images")
