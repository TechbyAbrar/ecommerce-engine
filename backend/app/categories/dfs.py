"""Deterministic in-memory DFS construction for category trees."""
from collections.abc import Iterable

from app.categories.models import Category


def build_category_tree(categories: Iterable[Category]) -> list[dict]:
    """Return active categories as a stable forest without recursive DB queries."""
    nodes: dict[object, dict] = {}
    for category in categories:
        nodes[category.id] = {
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "description": category.description,
            "parent_id": category.parent_id,
            "is_active": category.is_active,
            "created_at": category.created_at,
            "updated_at": category.updated_at,
            "children": [],
        }

    roots: list[dict] = []
    for category_id, node in nodes.items():
        parent_id = node["parent_id"]
        if parent_id is None or parent_id not in nodes or parent_id == category_id:
            roots.append(node)
        else:
            nodes[parent_id]["children"].append(node)

    def visit(node: dict) -> None:
        node["children"].sort(key=lambda child: (child["name"].casefold(), str(child["id"])))
        for child in node["children"]:
            visit(child)

    roots.sort(key=lambda node: (node["name"].casefold(), str(node["id"])))
    for root in roots:
        visit(root)
    return roots
