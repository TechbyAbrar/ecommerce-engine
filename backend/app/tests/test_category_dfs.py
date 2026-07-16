from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.categories.dfs import build_category_tree


def test_build_category_tree_orders_and_nests_categories() -> None:
    root_id = uuid4()
    child_id = uuid4()
    now = datetime.now(timezone.utc)
    root = SimpleNamespace(
        id=root_id,
        name="Root",
        slug="root",
        description=None,
        parent_id=None,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    child = SimpleNamespace(
        id=child_id,
        name="Child",
        slug="child",
        description=None,
        parent_id=root_id,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    tree = build_category_tree([child, root])

    assert [node["id"] for node in tree] == [root_id]
    assert [node["id"] for node in tree[0]["children"]] == [child_id]
