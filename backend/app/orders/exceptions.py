from app.core.exceptions import ConflictException, NotFoundException


class OrderNotFoundException(NotFoundException):
    error_code = "ORDER_NOT_FOUND"

    def __init__(self, message: str = "Order was not found"):
        super().__init__(message)


class OrderStateException(ConflictException):
    error_code = "INVALID_ORDER_STATE"


class InsufficientStockException(ConflictException):
    error_code = "INSUFFICIENT_STOCK"
