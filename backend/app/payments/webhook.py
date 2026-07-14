import hashlib
import hmac
import json
import os
import time

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses import SuccessResponse
from app.core.dependencies import get_db
from app.payments.exceptions import InvalidWebhookException
from app.payments.models import PaymentStatus
from app.payments.schemas import PaymentRead
from app.payments.service import PaymentService

router = APIRouter(prefix="/payments/webhooks", tags=["Payment webhooks"])


def _verify_stripe_signature(raw_body: bytes, signature: str | None) -> None:
    """Verify Stripe's timestamped v1 HMAC signature against the unparsed body."""
    secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not secret or not signature:
        raise InvalidWebhookException("Missing Stripe webhook signature configuration")
    values: dict[str, list[str]] = {}
    for part in signature.split(","):
        key, separator, value = part.partition("=")
        if separator:
            values.setdefault(key, []).append(value)
    try:
        timestamp = int(values["t"][0])
    except (KeyError, ValueError):
        raise InvalidWebhookException("Malformed Stripe signature")
    if abs(time.time() - timestamp) > 300:
        raise InvalidWebhookException("Expired Stripe webhook signature")
    signed_payload = str(timestamp).encode("ascii") + b"." + raw_body
    expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected, candidate) for candidate in values.get("v1", [])):
        raise InvalidWebhookException("Invalid Stripe webhook signature")


@router.post("/stripe", response_model=SuccessResponse[PaymentRead | None])
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    raw_body = await request.body()
    _verify_stripe_signature(raw_body, request.headers.get("Stripe-Signature"))
    try:
        event = json.loads(raw_body)
        intent = event["data"]["object"]
        transaction_id = intent["id"]
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise InvalidWebhookException("Malformed Stripe webhook event") from exc
    event_type = event.get("type")
    if event_type == "payment_intent.succeeded":
        payment_status = PaymentStatus.SUCCESS
    elif event_type == "payment_intent.payment_failed":
        payment_status = PaymentStatus.FAILED
    else:
        # Ignore other authenticated Stripe events without changing payment state.
        return SuccessResponse(message="Stripe event ignored", data=None)
    payment = await PaymentService(db).apply_webhook(transaction_id, payment_status, event)
    return SuccessResponse(message="Stripe webhook processed", data=payment)


@router.api_route("/bkash", methods=["GET", "POST"], response_model=SuccessResponse[PaymentRead])
async def bkash_callback(request: Request, db: AsyncSession = Depends(get_db)):
    # bKash completion is checked by server-side Execute Payment, rather than
    # trusting callback parameters that could be supplied by a browser.
    transaction_id = request.query_params.get("paymentID")
    if not transaction_id:
        try:
            body = await request.json()
            transaction_id = body.get("paymentID")
        except (json.JSONDecodeError, UnicodeDecodeError):
            transaction_id = None
    if not transaction_id:
        raise InvalidWebhookException("Missing bKash paymentID")
    payment = await PaymentService(db).process_bkash_callback(transaction_id)
    return SuccessResponse(message="bKash callback processed", data=payment)
