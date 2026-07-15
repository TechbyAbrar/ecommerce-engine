"""Pydantic request and response schemas for categories."""
import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    parent_id: uuid.UUID | None = None
    is_active: bool = True

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str) -> str:
        slug = value.strip().lower()
        if not _SLUG_PATTERN.fullmatch(slug):
            raise ValueError("Slug may contain lowercase letters, numbers, and single hyphens only")
        return slug


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    parent_id: uuid.UUID | None = None
    is_active: bool | None = None

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str | None) -> str | None:
        if value is None:
            return value
        slug = value.strip().lower()
        if not _SLUG_PATTERN.fullmatch(slug):
            raise ValueError("Slug may contain lowercase letters, numbers, and single hyphens only")
        return slug


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    parent_id: uuid.UUID | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CategoryTreeRead(CategoryRead):
    children: list["CategoryTreeRead"] = Field(default_factory=list)


CategoryTreeRead.model_rebuild()
