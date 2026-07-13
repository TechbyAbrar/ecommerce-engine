#app/core/security.py

from passlib.context import CryptContext

# New passwords use Argon2id. bcrypt remains enabled only to verify hashes
# already stored in the database, and is marked deprecated for migration.
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    default="argon2",
    deprecated=["bcrypt"],
)


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_and_update_password(
    plain_password: str, hashed_password: str
) -> tuple[bool, str | None]:
    """Verify a password and return a replacement hash when the scheme is deprecated."""
    # A bcrypt hash could only have been created from the first 72 bytes. Avoid
    # passing a longer password to bcrypt while allowing unlimited input for
    # Argon2id hashes.
    is_bcrypt_hash = hashed_password.startswith(("$2a$", "$2b$", "$2y$"))
    if is_bcrypt_hash and len(plain_password.encode("utf-8")) > 72:
        return False, None
    return pwd_context.verify_and_update(plain_password, hashed_password)
