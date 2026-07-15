import os
import time
from decimal import Decimal

import httpx

from app.payments.exceptions import PaymentProviderException
from app.payments.strategy import PaymentStrategy, ProviderResult


class BKashStrategy(PaymentStrategy):
    """bKash checkout adapter. The gateway URL and bearer token are environment-owned."""

    _id_token: str | None = None
    _token_expires_at: float = 0

    async def _headers(self) -> dict[str, str]:
        app_key = os.getenv("BKASH_APP_KEY")
        if not app_key:
            raise PaymentProviderException("bKash is not configured")
        token = await self._token()
        return {
            "Authorization": token,
            "X-App-Key": app_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _base_url(self) -> str:
        url = os.getenv("BKASH_BASE_URL")
        if not url:
            raise PaymentProviderException("bKash is not configured")
        return url.rstrip("/")

    async def _token(self) -> str:
        configured_token = os.getenv("BKASH_ID_TOKEN")
        if configured_token:
            return configured_token
        if type(self)._id_token and time.time() < type(self)._token_expires_at:
            return type(self)._id_token
        app_key = os.getenv("BKASH_APP_KEY")
        app_secret = os.getenv("BKASH_APP_SECRET")
        username = os.getenv("BKASH_USERNAME")
        password = os.getenv("BKASH_PASSWORD")
        if not all((app_key, app_secret, username, password)):
            raise PaymentProviderException("bKash credentials are not configured")
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self._base_url()}/checkout/token/grant",
                    json={"app_key": app_key, "app_secret": app_secret},
                    headers={"username": username, "password": password, "Content-Type": "application/json"},
                )
                response.raise_for_status()
                body = response.json()
        except httpx.HTTPError as exc:
            raise PaymentProviderException("bKash access token could not be created") from exc
        token = body.get("id_token")
        if not token:
            raise PaymentProviderException("bKash did not return an access token")
        type(self)._id_token = token
        type(self)._token_expires_at = time.time() + max(60, int(body.get("expires_in", 3600)) - 60)
        return token

    async def initiate(self, amount: Decimal, reference: str, return_url: str | None = None) -> ProviderResult:
        if not return_url:
            raise PaymentProviderException("bKash requires a callback URL")
        payload = {
            "amount": str(amount),
            "currency": "BDT",
            "intent": "sale",
            "merchantInvoiceNumber": reference,
            "callbackURL": return_url,
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    f"{self._base_url()}/checkout/create", json=payload, headers=await self._headers()
                )
                response.raise_for_status()
                body = response.json()
        except httpx.HTTPError as exc:
            raise PaymentProviderException("bKash checkout could not be created") from exc
        transaction_id = body.get("paymentID")
        if not transaction_id:
            raise PaymentProviderException("bKash did not return a payment ID")
        status = body.get("transactionStatus")
        return ProviderResult(transaction_id, status == "Completed", body, status in {"Cancelled", "Declined", "Expired", "Failed"})

    async def confirm(self, transaction_id: str, payment_method_id: str | None = None) -> ProviderResult:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    f"{self._base_url()}/checkout/execute",
                    json={"paymentID": transaction_id},
                    headers=await self._headers(),
                )
                response.raise_for_status()
                body = response.json()
        except httpx.HTTPError as exc:
            raise PaymentProviderException("bKash payment could not be executed") from exc
        status = body.get("transactionStatus")
        return ProviderResult(transaction_id, status == "Completed", body, status in {"Cancelled", "Declined", "Expired", "Failed"})
