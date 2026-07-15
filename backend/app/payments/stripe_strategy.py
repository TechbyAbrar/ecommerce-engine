import asyncio
from decimal import Decimal

import stripe

from app.core.config import settings
from app.payments.exceptions import PaymentProviderException
from app.payments.strategy import PaymentStrategy, ProviderResult


class StripeStrategy(PaymentStrategy):
    """Stripe PaymentIntent adapter using Stripe's official Python SDK."""

    def _api_key(self) -> str:
        if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_SECRET_KEY.get_secret_value():
            raise PaymentProviderException("Stripe is not configured")
        return settings.STRIPE_SECRET_KEY.get_secret_value()

    @staticmethod
    def _as_dict(payment_intent: stripe.PaymentIntent) -> dict:
        return payment_intent.to_dict()

    @staticmethod
    def _amount_in_minor_units(amount: Decimal, currency: str) -> int:
        # Stripe expects the smallest currency unit; these currencies have no
        # decimal minor unit. All other currently supported currencies use two.
        zero_decimal_currencies = {"bif", "clp", "djf", "gnf", "jpy", "kmf", "krw", "mga", "pyg", "rwf", "ugx", "vnd", "vuv", "xaf", "xof", "xpf"}
        multiplier = Decimal(1 if currency in zero_decimal_currencies else 100)
        minor_units = amount * multiplier
        if minor_units != minor_units.to_integral_value() or minor_units <= 0:
            raise PaymentProviderException("Order total is not valid for the configured Stripe currency")
        return int(minor_units)

    async def initiate(self, amount: Decimal, reference: str, return_url: str | None = None) -> ProviderResult:
        currency = settings.STRIPE_CURRENCY.lower()
        try:
            payment_intent = await asyncio.to_thread(
                stripe.PaymentIntent.create,
                api_key=self._api_key(),
                amount=self._amount_in_minor_units(amount, currency),
                currency=currency,
                metadata={"order_id": reference},
                automatic_payment_methods={"enabled": True},
                idempotency_key=f"payment-intent:{reference}",
            )
        except stripe.StripeError as exc:
            raise PaymentProviderException("Stripe payment intent could not be created") from exc
        body = self._as_dict(payment_intent)
        return ProviderResult(payment_intent.id, payment_intent.status == "succeeded", body, payment_intent.status == "canceled")

    async def confirm(self, transaction_id: str, payment_method_id: str | None = None) -> ProviderResult:
        try:
            if payment_method_id:
                payment_intent = await asyncio.to_thread(
                    stripe.PaymentIntent.confirm,
                    transaction_id,
                    api_key=self._api_key(),
                    payment_method=payment_method_id,
                )
            else:
                # Stripe.js may already have confirmed the intent. Retrieve it
                # server-side to make the database transition authoritative.
                payment_intent = await asyncio.to_thread(
                    stripe.PaymentIntent.retrieve, transaction_id, api_key=self._api_key()
                )
        except stripe.StripeError as exc:
            raise PaymentProviderException("Stripe payment status could not be verified") from exc
        body = self._as_dict(payment_intent)
        return ProviderResult(transaction_id, payment_intent.status == "succeeded", body, payment_intent.status == "canceled")
