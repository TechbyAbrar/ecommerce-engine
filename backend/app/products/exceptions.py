from app.core.exceptions import AppException, ConflictException, NotFoundException


class ProductNotFoundException(NotFoundException):
    error_code = "PRODUCT_NOT_FOUND"

    def __init__(self, message: str = "Product was not found"):
        super().__init__(message)


class ProductSKUExistsException(ConflictException):
    error_code = "PRODUCT_SKU_EXISTS"


class ProductImageValidationException(AppException):
    status_code = 422
    error_code = "PRODUCT_IMAGE_INVALID"

    def __init__(self, message: str):
        super().__init__(message)
