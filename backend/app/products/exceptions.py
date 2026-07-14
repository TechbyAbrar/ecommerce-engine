from app.core.exceptions import ConflictException, NotFoundException


class ProductNotFoundException(NotFoundException):
    error_code = "PRODUCT_NOT_FOUND"

    def __init__(self, message: str = "Product was not found"):
        super().__init__(message)


class ProductSKUExistsException(ConflictException):
    error_code = "PRODUCT_SKU_EXISTS"

    def __init__(self, message: str = "A product with this SKU already exists"):
        super().__init__(message)
