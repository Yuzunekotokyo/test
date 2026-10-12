"""Abstract exchange adapter. Implement this for PopDEX; the engine never
talks to an exchange any other way, so the strategy can be tested on paper."""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import BookTop, Fill, Order, OrderType, Position, Side


class ExchangeAdapter(ABC):
    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def close(self) -> None: ...

    @abstractmethod
    async def book_top(self, symbol: str) -> BookTop: ...

    @abstractmethod
    async def funding_rate(self, symbol: str) -> float:
        """Current (or predicted next) funding rate as a fraction per interval."""

    @abstractmethod
    async def place_order(
        self, symbol: str, side: Side, type: OrderType, size: float,
        price: float | None = None, post_only: bool = True, reduce_only: bool = False,
    ) -> Order: ...

    @abstractmethod
    async def cancel_order(self, order_id: str) -> None: ...

    @abstractmethod
    async def cancel_all(self, symbol: str) -> None: ...

    @abstractmethod
    async def open_orders(self, symbol: str) -> list[Order]: ...

    @abstractmethod
    async def poll_fills(self, symbol: str) -> list[Fill]:
        """Return fills since the previous call. Each fill is returned once."""

    @abstractmethod
    async def position(self, symbol: str) -> Position: ...

    @abstractmethod
    async def equity(self) -> float:
        """Account equity in USD (collateral + unrealized)."""
