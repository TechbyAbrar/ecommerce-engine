from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

MONEY_QUANTUM = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def calculate_subtotal(unit_price: Decimal, quantity: int) -> Decimal:
    if quantity < 1:
        raise ValueError("Quantity must be at least one")
    return money(unit_price * quantity)


def calculate_total(subtotals: Iterable[Decimal]) -> Decimal:
    return money(sum(subtotals, Decimal("0")))
