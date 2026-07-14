import uuid
from collections import Counter

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.orders.algorithms import calculate_subtotal, calculate_total
from app.orders.exceptions import InsufficientStockException, OrderNotFoundException, OrderStateException
from app.orders.models import Order, OrderItem, OrderStatus
from app.orders.repository import OrderRepository
from app.orders.schemas import OrderCreate, OrderRead
from app.products.models import Product, ProductStatus
from app.products.cache import product_cache


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = OrderRepository(db)

    async def create(self, user: User, data: OrderCreate) -> OrderRead:
        quantities = Counter(item.product_id for item in data.items)
        if len(quantities) != len(data.items):
            raise OrderStateException("Each product can appear only once in an order")
        products = list(await self.db.scalars(select(Product).where(Product.id.in_(quantities))))
        if len(products) != len(quantities):
            raise OrderStateException("One or more products do not exist")
        by_id = {product.id: product for product in products}
        items: list[OrderItem] = []
        subtotals = []
        for requested in data.items:
            product = by_id[requested.product_id]
            if product.status != ProductStatus.ACTIVE:
                raise OrderStateException("Inactive products cannot be ordered")
            subtotal = calculate_subtotal(product.price, requested.quantity)
            subtotals.append(subtotal)
            items.append(OrderItem(product_id=product.id, quantity=requested.quantity, price=product.price, subtotal=subtotal))
        order = Order(user_id=user.id, total_amount=calculate_total(subtotals), items=items)
        return OrderRead.model_validate(await self.repository.create(order))

    async def get(self, user: User, order_id: uuid.UUID) -> OrderRead:
        order = await self.repository.get(order_id, user.id)
        if not order:
            raise OrderNotFoundException()
        return OrderRead.model_validate(order)

    async def list_for_user(self, user: User) -> list[OrderRead]:
        return [OrderRead.model_validate(order) for order in await self.repository.list_for_user(user.id)]

    async def finalize_paid_order(self, order_id: uuid.UUID) -> Order:
        order = await self.repository.get(order_id, lock=True)
        if not order:
            raise OrderNotFoundException()
        if order.status == OrderStatus.PAID:
            return order
        if order.status != OrderStatus.PENDING:
            raise OrderStateException("Only pending orders can be paid")
        product_ids = sorted((item.product_id for item in order.items), key=str)
        products = list(await self.db.scalars(select(Product).where(Product.id.in_(product_ids)).with_for_update()))
        by_id = {product.id: product for product in products}
        for item in order.items:
            product = by_id.get(item.product_id)
            if not product or product.status != ProductStatus.ACTIVE or product.stock < item.quantity:
                raise InsufficientStockException("A product no longer has sufficient stock")
        for item in order.items:
            by_id[item.product_id].stock -= item.quantity
        await self.repository.mark_paid(order)
        for product_id in product_ids:
            await product_cache.delete(f"products:detail:{product_id}")
        await product_cache.invalidate_lists()
        return order
