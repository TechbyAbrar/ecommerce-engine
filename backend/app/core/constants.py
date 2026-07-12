#app/core/constants.py
"""
Application-wide constants that don't belong to a single domain.
"""

# --- Auth / token related ---
BEARER_PREFIX = "Bearer"
TOKEN_URL = "/api/v1/auth/login"

# --- Pagination defaults ---
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# --- Misc ---
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
