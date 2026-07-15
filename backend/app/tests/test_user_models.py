from sqlalchemy.orm import configure_mappers

from app.auth.models import User
from app.common.enums import UserRole
from app.users.models import UserDetails


def test_user_details_relationship_is_bidirectional() -> None:
    configure_mappers()

    assert User.details.property.mapper.class_ is UserDetails
    assert UserDetails.user.property.mapper.class_ is User


def test_user_role_values_are_persisted_values() -> None:
    role_type = User.__table__.c.role.type

    assert list(role_type.enums) == [role.value for role in UserRole]
