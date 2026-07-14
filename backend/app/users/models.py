#app/users/models.py

"""
UserDetails / Address / UserLoyalty models for the ecommerce platform.

===========================================================================
HIGH-VOLUME PRODUCTION DESIGN DECISIONS (read this before changing PK types)
===========================================================================

1. BIGINT surrogate PKs instead of random UUID PKs on high-write tables.
   Your `users` table uses a random UUID(v4) PK, which is fine for a table
   with moderate insert rate (signups). But `addresses` and `user_details`
   can grow much larger and be written to far more often (every checkout,
   every profile edit). A random UUID PK means every insert hits a random
   point in the B-tree index -> heavy page splits, index bloat, and worse
   buffer-cache locality at scale. A BIGINT identity column is monotonically
   increasing -> inserts are always at the right edge of the index -> far
   cheaper on CPU/IO. `users.id` stays UUID (unchanged, not our call to make
   here) and we just FK to it normally.

2. Externally-exposed IDs still use UUID (`public_id`) where the row is
   addressable via a public/customer-facing API (e.g. GET /addresses/{id}),
   so we don't leak sequential IDs (enumeration / row-count leakage). This
   keeps the fast BIGINT PK internally while staying safe externally.
   `user_details` doesn't need its own public_id: it's always looked up via
   `user_id` (already a non-sequential UUID) in an authenticated context.

3. Loyalty points are split into a separate `user_loyalty` table instead of
   living as a column on `user_details`. Points get written on every single
   order/refund -- if that lived in the same row as profile fields (phone,
   DOB, language, etc.), every purchase would dirty the whole profile row,
   bloating the table and forcing autovacuum to work much harder on data
   that's otherwise read-heavy/write-light. Isolating hot-write columns
   into their own narrow table is a standard high-volume Postgres pattern.

4. `tier` on user_loyalty uses String + CHECK instead of a native Postgres
   ENUM. Native enums are cheap to read but adding a new value later
   (`ALTER TYPE ... ADD VALUE`) has migration gotchas (can't run inside a
   transaction on older PG, needs care under concurrent load). Loyalty tiers
   are a business concept that changes more often than e.g. gender/address
   type, so a VARCHAR + CHECK constraint trades a few bytes for painless
   migrations. Stable, rarely-changing enums (Gender, AddressType) keep
   native ENUM since read frequency is high and change frequency is ~zero.

5. Every index below is deliberately justified. No boolean column gets a
   full index (e.g. no plain index on `newsletter_subscribed`) -- low
   selectivity booleans are expensive to maintain on every write for
   little query benefit; if you need "all subscribed users" at scale,
   pull that from an analytics/read-replica query or a periodic materialized
   view, not a live index on the OLTP table.

6. Soft delete (`is_active`) on addresses, not hard delete. Addresses may be
   referenced by historical orders. (Orders should store a JSON *snapshot*
   of the address at order time -- never a live FK -- so a user editing/
   deleting an address never mutates past order history. That snapshot logic
   belongs in `orders/models.py`, not here.) Soft-deleting means we never pay
   for cascading deletes or dangling-default cleanup under write load.

7. Timestamps are TIMESTAMPTZ (`DateTime(timezone=True)`), matching `User`.
   `updated_at` uses `onupdate=func.now()` (DB-side) instead of an
   app-side Python value, so it's set atomically by Postgres itself with
   no extra round trip and no clock-skew risk across app instances.

8. Migration note (not code, but critical for high volume): when you add
   these tables/indexes via Alembic against a table that already has data,
   run `CREATE INDEX CONCURRENTLY` (Alembic: `op.create_index(...,
   postgresql_concurrently=True)`, executed outside a transaction block)
   so index creation doesn't take a blocking lock on a live production table.
===========================================================================
"""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


# --------------------------------------------------------------------------
# Enums
# --------------------------------------------------------------------------
class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNDISCLOSED = "undisclosed"


class AddressType(str, enum.Enum):
    SHIPPING = "shipping"
    BILLING = "billing"



LOYALTY_TIERS = ("bronze", "silver", "gold", "platinum")


class UserDetails(Base):
    __tablename__ = "user_details"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[Gender | None] = mapped_column(
        Enum(Gender, name="gender"), nullable=True
    )
    avatar_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # Denormalized "current default" pointers so rendering a checkout page
    # never needs to scan addresses -- one row fetch via PK. SET NULL keeps
    # deleting/deactivating an address from ever touching this row's other
    # columns or cascading unexpectedly.
    default_shipping_address_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("addresses.id", ondelete="SET NULL"), nullable=True
    )
    default_billing_address_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("addresses.id", ondelete="SET NULL"), nullable=True
    )

    preferred_language: Mapped[str] = mapped_column(
        String(10), server_default="en", nullable=False
    )
    preferred_currency: Mapped[str] = mapped_column(
        String(3), server_default="USD", nullable=False
    )
    newsletter_subscribed: Mapped[bool] = mapped_column(
        Boolean, server_default="false", nullable=False
    )
    marketing_opt_in: Mapped[bool] = mapped_column(
        Boolean, server_default="false", nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="details", uselist=False)
    loyalty = relationship(
        "UserLoyalty",
        back_populates="user_details",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    addresses = relationship(
        "Address",
        back_populates="user_details",
        foreign_keys="Address.user_details_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    default_shipping_address = relationship(
        "Address", foreign_keys=[default_shipping_address_id], post_update=True
    )
    default_billing_address = relationship(
        "Address", foreign_keys=[default_billing_address_id], post_update=True
    )

    __table_args__ = (
        CheckConstraint(
            "length(preferred_currency) = 3", name="ck_user_details_currency_iso_len"
        ),
        # Partial index: only rows with a phone number are worth indexing
        # (used for OTP/support lookups). Cuts index size vs. a full index.
        Index(
            "ix_user_details_phone_number",
            "phone_number",
            postgresql_where=(phone_number.isnot(None)),
        ),
    )

    def __repr__(self) -> str:
        return f"<UserDetails id={self.id} user_id={self.user_id}>"


# --------------------------------------------------------------------------
# UserLoyalty (1:1 with UserDetails) -- isolated because it's write-hot
# --------------------------------------------------------------------------
class UserLoyalty(Base):
    __tablename__ = "user_loyalty"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    user_details_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user_details.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    points: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    tier: Mapped[str] = mapped_column(
        String(20), server_default="bronze", nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user_details = relationship("UserDetails", back_populates="loyalty")

    __table_args__ = (
        CheckConstraint("points >= 0", name="ck_user_loyalty_points_non_negative"),
        CheckConstraint(
            f"tier IN {LOYALTY_TIERS}", name="ck_user_loyalty_tier_valid"
        ),
    )

    def __repr__(self) -> str:
        return f"<UserLoyalty user_details_id={self.user_details_id} tier={self.tier}>"


# --------------------------------------------------------------------------
# Address (1:many with UserDetails)
# --------------------------------------------------------------------------
class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Safe external identifier (see design note #2). Expose THIS in API
    # responses/URLs, never the internal bigint `id`.
    public_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False
    )

    user_details_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user_details.id", ondelete="CASCADE"), nullable=False
    )

    address_type: Mapped[AddressType] = mapped_column(
        Enum(AddressType, name="address_type"), nullable=False
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean, server_default="false", nullable=False
    )
    # Soft delete -- see design note #6. Filter on this in the repository
    # layer instead of ever issuing a DELETE for a user-facing "remove address".
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default="true", nullable=False
    )

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)

    line1: Mapped[str] = mapped_column(String(255), nullable=False)
    line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)  # ISO 3166-1 alpha-2

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user_details = relationship(
        "UserDetails", back_populates="addresses", foreign_keys=[user_details_id]
    )

    __table_args__ = (
        CheckConstraint("length(country_code) = 2", name="ck_addresses_country_iso_len"),
        # Core query: "all active addresses for this user, of this type" --
        # a single composite index covers the entire checkout-page query.
        Index(
            "ix_addresses_user_type_active",
            "user_details_id",
            "address_type",
            postgresql_where=(is_active.is_(True)),
        ),
        # DB-enforced invariant: at most one default address per (user, type)
        # among active rows -- race-safe, no app-level locking needed.
        Index(
            "uq_addresses_one_default_per_type",
            "user_details_id",
            "address_type",
            unique=True,
            postgresql_where=(is_default.is_(True) & is_active.is_(True)),
        ),
    )

    def __repr__(self) -> str:
        return f"<Address id={self.id} type={self.address_type} city={self.city}>"