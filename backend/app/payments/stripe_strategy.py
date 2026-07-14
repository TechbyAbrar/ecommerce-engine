import os
from decimal import Decimal

import httpx

from app.payments.exceptions import PaymentProviderException
from app.payments.strategy import PaymentStrategy, ProviderResult


class StripeStrategy(PaymentStrategy):
    base_url = "https://api.stripe.com/v1"

    def _headers(self) -> dict[str, str]:
        key = os.getenv("STRIPE_SECRET_KEY")
        if not key:
            raise PaymentProviderException("Stripe is not configured")
        return {"Authorization": f"Bearer {key}"}

    async def initiate(self, amount: Decimal, reference: str, return_url: str | None = None) -> ProviderResult:
        payload = {
            "amount": str(int(amount * 100)),
            "currency": os.getenv("STRIPE_CURRENCY", "usd").lower(),
            "metadata[order_id]": reference,
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    f"{self.base_url}/payment_intents",
                    data=payload,
                    headers={**self._headers(), "Idempotency-Key": f"order:{reference}"},
                )
                response.raise_for_status()
                body = response.json()
        except httpx.HTTPError as exc:
            raise PaymentProviderException("Stripe payment intent could not be created") from exc
        return ProviderResult(body["id"], body.get("status") == "succeeded", body)

    async def confirm(self, transaction_id: str, payment_method_id: str | None = None) -> ProviderResult:
        payload = {"payment_method": payment_method_id} if payment_method_id else None
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    f"{self.base_url}/payment_intents/{transaction_id}/confirm",
                    data=payload,
                    headers=self._headers(),
                )
                response.raise_for_status()
                body = response.json()
        except httpx.HTTPError as exc:
            raise PaymentProviderException("Stripe payment status could not be verified") from exc
        return ProviderResult(transaction_id, body.get("status") == "succeeded", body)
