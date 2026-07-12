#app/common/utils.py
"""
Small, generic helper functions used across domains.
"""
import uuid
from datetime import datetime, timezone


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Timezone-aware current UTC time (avoid naive datetimes for token exp, etc)."""
    return datetime.now(timezone.utc)


def mask_email(email: str) -> str:
    """e.g. 'abraham@example.com' -> 'ab*****@example.com' (useful for logs)."""
    local, _, domain = email.partition("@")
    if len(local) <= 2:
        masked = local[0] + "*" * (len(local) - 1)
    else:
        masked = local[:2] + "*" * (len(local) - 2)
    return f"{masked}@{domain}"
