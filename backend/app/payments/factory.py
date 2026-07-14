from app.payments.bkash_strategy import BKashStrategy
from app.payments.models import PaymentProvider
from app.payments.stripe_strategy import StripeStrategy
from app.payments.strategy import PaymentStrategy


class PaymentStrategyFactory:
    @staticmethod
    def get(provider: PaymentProvider) -> PaymentStrategy:
        if provider == PaymentProvider.STRIPE:
            return StripeStrategy()
        if provider == PaymentProvider.BKASH:
            return BKashStrategy()
        raise ValueError(f"Unsupported payment provider: {provider}")
