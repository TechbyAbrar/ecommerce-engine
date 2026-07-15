import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.orders.exceptions import OrderNotFoundException
from app.orders.models import OrderStatus
from app.orders.repository import OrderRepository
from app.orders.service import OrderService
from app.payments.exceptions import PaymentNotFoundException, PaymentStateException
from app.payments.models import PaymentProvider
from app.payments.factory import PaymentStrategyFactory
from app.payments.models import Payment, PaymentStatus
from app.payments.repository import PaymentRepository
from app.payments.schemas import PaymentInitiate, PaymentRead


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = PaymentRepository(db)
        self.orders = OrderRepository(db)

    async def initiate(self, user: User, order_id: uuid.UUID, data: PaymentInitiate) -> PaymentRead:
        order = await self.orders.get(order_id, user.id)
        if not order:
            raise OrderNotFoundException()
        if order.status != OrderStatus.PENDING:
            raise PaymentStateException("Only pending orders can be paid")
        # An order has only one active payment attempt. This prevents a user
        # from opening two provider checkouts and being charged twice.
        existing_payment = await self.repository.get_pending_for_order(order.id)
        if existing_payment:
            return PaymentRead.model_validate(existing_payment)
        result = await PaymentStrategyFactory.get(data.provider).initiate(order.total_amount, str(order.id), data.return_url)
        try:
            payment = await self.repository.create(order.id, data.provider, result.transaction_id, result.raw_response)
        except IntegrityError:
            # Stripe's idempotency key returns the same PaymentIntent for
            # concurrent initiate requests. Reuse its existing local record.
            await self.db.rollback()
            payment = await self.repository.get_by_transaction(result.transaction_id)
            if not payment:
                raise
        if result.successful:
            await self._mark_success(payment, result.raw_response)
        return PaymentRead.model_validate(payment)

    async def confirm(
        self, user: User, payment_id: uuid.UUID, payment_method_id: str | None = None
    ) -> PaymentRead:
        payment = await self.repository.get(payment_id, lock=True)
        if not payment:
            raise PaymentNotFoundException()
        order = await self.orders.get(payment.order_id, user.id)
        if not order:
            raise PaymentNotFoundException()
        if payment.status == PaymentStatus.SUCCESS:
            return PaymentRead.model_validate(payment)
        result = await PaymentStrategyFactory.get(payment.provider).confirm(
            payment.transaction_id, payment_method_id
        )
        if result.successful:
            await self._mark_success(payment, result.raw_response)
        elif result.failed:
            await self.repository.set_status(payment, PaymentStatus.FAILED, result.raw_response)
            await self.db.commit()
        return PaymentRead.model_validate(payment)

    async def list_for_user(self, user: User) -> list[PaymentRead]:
        order_ids = await self.orders.list_ids_for_user(user.id)
        payments = await self.repository.list_for_order_ids(order_ids)
        return [PaymentRead.model_validate(payment) for payment in payments]

    async def apply_webhook(
        self, transaction_id: str, status: PaymentStatus, raw_response: dict
    ) -> PaymentRead:
        """Apply a verified provider event exactly once within one DB transaction."""
        payment = await self.repository.get_by_transaction(transaction_id, lock=True)
        if not payment:
            raise PaymentNotFoundException()
        if payment.status == PaymentStatus.SUCCESS:
            return PaymentRead.model_validate(payment)

        if status == PaymentStatus.SUCCESS:
            # finalize_paid_order locks the order and its products, then stock,
            # order status, and payment status commit together below.
            await self._mark_success(payment, raw_response)
        elif status == PaymentStatus.FAILED:
            await self.repository.set_status(payment, PaymentStatus.FAILED, raw_response)
            await self.db.commit()
        return PaymentRead.model_validate(payment)

    async def process_bkash_callback(self, transaction_id: str) -> PaymentRead:
        """Execute bKash server-side; browser callback data is never trusted."""
        payment = await self.repository.get_by_transaction(transaction_id, lock=True)
        if not payment or payment.provider != PaymentProvider.BKASH:
            raise PaymentNotFoundException()
        if payment.status == PaymentStatus.SUCCESS:
            return PaymentRead.model_validate(payment)
        result = await PaymentStrategyFactory.get(payment.provider).confirm(payment.transaction_id)
        if result.successful:
            await self._mark_success(payment, result.raw_response)
        elif result.failed:
            await self.repository.set_status(payment, PaymentStatus.FAILED, result.raw_response)
            await self.db.commit()
        return PaymentRead.model_validate(payment)

    async def _mark_success(self, payment: Payment, raw_response: dict) -> None:
        await OrderService(self.db).finalize_paid_order(payment.order_id)
        await self.repository.set_status(payment, PaymentStatus.SUCCESS, raw_response)
        await self.db.commit()
