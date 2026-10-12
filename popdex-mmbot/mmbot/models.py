"""Core data types shared by the strategy, risk layer and exchange adapters."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"

    def opposite(self) -> "Side":
        return Side.SELL if self is Side.BUY else Side.BUY

    @property
    def sign(self) -> int:
        return 1 if self is Side.BUY else -1


class OrderType(str, Enum):
    LIMIT = "limit"      # maker (post-only) order
    MARKET = "market"    # taker order


@dataclass
class Quote:
    """A single price/size the strategy wants resting on the book."""
    side: Side
    price: float
    size: float


@dataclass
class Order:
    id: str
    symbol: str
    side: Side
    type: OrderType
    price: float | None
    size: float
    filled: float = 0.0
    post_only: bool = True
    created_at: float = field(default_factory=time.time)
    status: str = "open"  # open | filled | cancelled | rejected

    @property
    def remaining(self) -> float:
        return max(self.size - self.filled, 0.0)


@dataclass
class Fill:
    order_id: str
    symbol: str
    side: Side
    price: float
    size: float
    fee: float            # negative value = rebate received
    is_maker: bool
    ts: float = field(default_factory=time.time)


@dataclass
class Position:
    symbol: str
    size: float = 0.0           # signed: + long, - short (in base units)
    entry_price: float = 0.0
    realized_pnl: float = 0.0
    fees_paid: float = 0.0      # cumulative; negative = net rebates

    @property
    def notional(self) -> float:
        return abs(self.size) * self.entry_price

    def unrealized(self, mark: float) -> float:
        return self.size * (mark - self.entry_price)

    def apply_fill(self, fill: Fill) -> None:
        """Update position with a fill, booking realized PnL on reductions."""
        self.fees_paid += fill.fee
        delta = fill.size * fill.side.sign
        if self.size == 0 or (self.size > 0) == (delta > 0):
            # increasing / opening in the same direction -> weighted entry
            total = abs(self.size) + abs(delta)
            self.entry_price = (
                abs(self.size) * self.entry_price + abs(delta) * fill.price
            ) / total
            self.size += delta
            return
        # reducing or flipping
        closing = min(abs(delta), abs(self.size))
        direction = 1 if self.size > 0 else -1
        self.realized_pnl += closing * (fill.price - self.entry_price) * direction
        self.size += delta
        if abs(self.size) < 1e-12:
            self.size = 0.0
            self.entry_price = 0.0
        elif (self.size > 0) != (direction > 0):
            # flipped through zero: remainder opens at the fill price
            self.entry_price = fill.price


@dataclass
class BookTop:
    bid: float
    ask: float
    ts: float = field(default_factory=time.time)

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2

    @property
    def spread_bps(self) -> float:
        return (self.ask - self.bid) / self.mid * 1e4
