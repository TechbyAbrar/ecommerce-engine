from app.auth.dependencies import require_roles
from app.common.enums import UserRole

require_admin = require_roles(UserRole.ADMIN)
