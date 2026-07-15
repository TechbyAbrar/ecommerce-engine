"""Category tree cache backed by the application's existing Redis cache."""
from typing import Any

from app.products.cache import product_cache

_TREE_KEY = "categories:tree"


async def get_tree() -> Any | None:
    return await product_cache.get_json(_TREE_KEY)


async def set_tree(value: Any) -> None:
    await product_cache.set_json(_TREE_KEY, value)


async def invalidate_tree() -> None:
    await product_cache.delete(_TREE_KEY)
