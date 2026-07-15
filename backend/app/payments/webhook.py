import asyncio
import json

import stripe

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses import SuccessResponse
from app.core.config import settings
from app.core.dependencies import get_db
from app.payments.exceptions import InvalidWebhookException
from app.payments.models import PaymentStatus
from app.payments.schemas import PaymentRead
from app.payments.service import PaymentService

router = APIRouter(prefix="/payments/webhooks", tags=["Payment webhooks"])


async def _construct_stripe_event(raw_body: bytes, signature: str | None) -> stripe.Event:
    """Verify Stripe's signature with the official SDK before parsing the event."""
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    if not webhook_secret or not signature:
        raise InvalidWebhookException("Missing Stripe webhook signature configuration")
    try:
        return await asyncio.to_thread(
            stripe.Webhook.construct_event,
            raw_body,
            signature,
            webhook_secret.get_secret_value(),
        )
    except (ValueError, AttributeError, stripe.SignatureVerificationError) as exc:
        raise InvalidWebhookException("Invalid Stripe webhook signature")


@router.post("/stripe", response_model=SuccessResponse[PaymentRead | None])
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    raw_body = await request.body()
    event = await _construct_stripe_event(raw_body, request.headers.get("Stripe-Signature"))
    try:
        intent = event["data"]["object"]
        transaction_id = intent["id"]
    except (KeyError, TypeError) as exc:
        raise InvalidWebhookException("Malformed Stripe webhook event") from exc
    event_type = event.get("type")
    if event_type == "payment_intent.succeeded":
        payment_status = PaymentStatus.SUCCESS
    elif event_type == "payment_intent.payment_failed":
        payment_status = PaymentStatus.FAILED
    else:
        # Ignore other authenticated Stripe events without changing payment state.
        return SuccessResponse(message="Stripe event ignored", data=None)
    payment = await PaymentService(db).apply_webhook(
        transaction_id, payment_status, event.to_dict()
    )
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
