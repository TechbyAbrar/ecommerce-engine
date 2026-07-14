from fastapi import status

from app.core.exceptions import AppException, ConflictException, NotFoundException


class PaymentNotFoundException(NotFoundException):
    error_code = "PAYMENT_NOT_FOUND"


class PaymentProviderException(AppException):
    status_code = status.HTTP_502_BAD_GATEWAY
    error_code = "PAYMENT_PROVIDER_ERROR"


class PaymentStateException(ConflictException):
    error_code = "INVALID_PAYMENT_STATE"


class InvalidWebhookException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "INVALID_WEBHOOK"
