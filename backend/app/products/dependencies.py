from fastapi import Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError

from app.auth.dependencies import require_roles
from app.common.enums import UserRole
from app.products.schemas import ProductCreate, ProductUpdate

require_admin = require_roles(UserRole.ADMIN, UserRole.SUPERUSER)


async def _product_payload(request: Request, fields: set[str]) -> dict[str, object]:
    if request.headers.get("content-type", "").split(";", 1)[0] == "application/json":
        payload = await request.json()
        return payload if isinstance(payload, dict) else {}
    form = await request.form()
    return {field: form[field] for field in fields if field in form}


async def _parse_product(request: Request, schema: type[BaseModel], fields: set[str]) -> BaseModel:
    try:
        return schema.model_validate(await _product_payload(request, fields))
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


async def product_create_data(request: Request) -> ProductCreate:
    return await _parse_product(request, ProductCreate, set(ProductCreate.model_fields))  # type: ignore[return-value]


async def product_update_data(request: Request) -> ProductUpdate:
    return await _parse_product(request, ProductUpdate, set(ProductUpdate.model_fields))  # type: ignore[return-value]
