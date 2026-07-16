"""Local storage for product image originals."""
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.products.exceptions import ProductImageValidationException

_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def _matches_content_type(content_type: str, content: bytes) -> bool:
    if content_type == "image/jpeg":
        return content.startswith(b"\xff\xd8\xff")
    if content_type == "image/png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    if content_type == "image/webp":
        return len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP"
    return False


@dataclass(frozen=True)
class StoredProductImage:
    file_path: str
    original_filename: str
    content_type: str
    file_size: int


class ProductImageStorage:
    def __init__(self, storage_path: str | Path | None = None) -> None:
        self.root = Path(storage_path or settings.PRODUCT_IMAGE_STORAGE_PATH)

    async def validate(self, upload: UploadFile) -> None:
        await self._validated_content(upload)
        await upload.seek(0)

    async def save(self, upload: UploadFile) -> StoredProductImage:
        try:
            content_type, content = await self._validated_content(upload)

            filename = f"{uuid.uuid4()}{_EXTENSIONS[content_type]}"
            destination = self.root / filename
            destination.parent.mkdir(parents=True, exist_ok=True)
            try:
                destination.write_bytes(content)
            except OSError as exc:
                raise RuntimeError("Unable to save product image") from exc

            return StoredProductImage(
                file_path=destination.as_posix(),
                original_filename=Path(upload.filename or filename).name[:255],
                content_type=content_type,
                file_size=len(content),
            )
        finally:
            await upload.close()

    async def _validated_content(self, upload: UploadFile) -> tuple[str, bytes]:
        content_type = upload.content_type or ""
        if content_type not in settings.PRODUCT_IMAGE_ALLOWED_CONTENT_TYPES:
            raise ProductImageValidationException("Only JPEG, PNG, and WebP images are allowed")

        content = await upload.read(settings.PRODUCT_IMAGE_MAX_SIZE_BYTES + 1)
        if not content:
            raise ProductImageValidationException("Image files cannot be empty")
        if len(content) > settings.PRODUCT_IMAGE_MAX_SIZE_BYTES:
            raise ProductImageValidationException("Image file exceeds the maximum allowed size")
        if not _matches_content_type(content_type, content):
            raise ProductImageValidationException("Image content does not match its declared MIME type")
        return content_type, content

    def delete(self, file_path: str) -> None:
        path = Path(file_path)
        try:
            path.relative_to(self.root)
        except ValueError:
            return
        path.unlink(missing_ok=True)
