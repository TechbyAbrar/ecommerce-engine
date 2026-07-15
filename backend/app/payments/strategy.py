from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class ProviderResult:
    transaction_id: str
    successful: bool
    raw_response: dict[str, Any]
    failed: bool = False


class PaymentStrategy(ABC):
    @abstractmethod
    async def initiate(self, amount: Decimal, reference: str, return_url: str | None = None) -> ProviderResult:
        """Create a provider-side payment and return its canonical transaction ID."""

    @abstractmethod
    async def confirm(self, transaction_id: str, payment_method_id: str | None = None) -> ProviderResult:
        """Query or execute a provider-side payment."""
